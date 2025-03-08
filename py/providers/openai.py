from collections.abc import Sequence, Mapping, Iterator
import urllib.request
import os

if "VIMAI_DUMMY_IMPORT" in os.environ:
    from py.types import Message, ResponseChunk, AIUtils, AIProvider

# TODO: each provider should provide it's error handling
# TODO: each provider should take care of it's default options
# TODO: how to properly extend AIProvider from types.py
class OpenAIProvider(AIProvider):

    def __init__(self, options: Mapping[str, str], utils: AIUtils) -> None:
        self.options = options
        self.utils = utils

    def request(self, messages: Sequence[Message]) -> Iterator[ResponseChunk]:
        options = self.options
        openai_options = self._make_openai_options(options)
        http_options = {
            'request_timeout': float(options['request_timeout']),
            'enable_auth': bool(int(options['enable_auth'])),
            'token_file_path': options['token_file_path'],
        }
        request = {
            'messages': messages,
            **openai_options
        }
        self.utils.print_debug("[engine-chat] request: {}", request)
        url = options['endpoint_url']
        response = self._openai_request(url, request, http_options)

        def _choices(resp):
            choices = resp.get('choices', [{}])

            # NOTE choices may exist in the response, but be an empty list.
            if not choices:
                return [{}]

            return choices

        def map_chunk_no_stream(resp) -> ResponseChunk:
            self.utils.print_debug("[engine-chat] response: {}", resp)
            content = _choices(resp)[0].get('message', {}).get('content', '')
            return {'type': 'content', 'content': content}

        def map_chunk_stream(resp) -> ResponseChunk:
            self.utils.print_debug("[engine-chat] response: {}", resp)
            content = _choices(resp)[0].get('delta', {}).get('content', '')
            return {'type': 'content', 'content': content}

        map_chunk = map_chunk_stream if openai_options['stream'] else map_chunk_no_stream

        return map(map_chunk, response)

    def _load_api_key(self):
        raw_api_key = self.utils.load_api_key("OPENAI_API_KEY", self.options['token_file_path'])
        # The text is in format of "<api key>,<org id>" and the
        # <org id> part is optional
        elements = raw_api_key.strip().split(",")
        api_key = elements[0].strip()
        org_id = None

        if len(elements) > 1:
            org_id = elements[1].strip()

        return (api_key, org_id)

    def _make_openai_options(self, options):
        max_tokens = int(options['max_tokens'])
        max_completion_tokens = int(options['max_completion_tokens'])
        result = {
            'model': options['model'],
            'temperature': float(options['temperature']),
            'stream': int(options['stream']) == 1,
        }
        if max_tokens > 0:
            result['max_tokens'] = max_tokens
        if max_completion_tokens > 0:
            result['max_completion_tokens'] = max_completion_tokens
        return result

    def _make_http_options(self, options):
        return {
            'request_timeout': float(options['request_timeout']),
            'enable_auth': bool(int(options['enable_auth'])),
            'token_file_path': options['token_file_path'],
        }

    def _openai_request(self, url, data, options):
        OPENAI_RESP_DATA_PREFIX = 'data: '
        OPENAI_RESP_DONE = '[DONE]'

        enable_auth=options['enable_auth']
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VimAI",
        }
        if enable_auth:
            (OPENAI_API_KEY, OPENAI_ORG_ID) = self._load_api_key()
            headers['Authorization'] = f"Bearer {OPENAI_API_KEY}"

            if OPENAI_ORG_ID is not None:
                headers["OpenAI-Organization"] =  f"{OPENAI_ORG_ID}"

        request_timeout=options['request_timeout']
        req = urllib.request.Request(
            url,
            data=json.dumps({ **data }).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=request_timeout) as response:
            if not data.get('stream', 0):
                yield json.loads(response.read().decode())
                return
            for line_bytes in response:
                line = line_bytes.decode("utf-8", errors="replace")
                if line.startswith(OPENAI_RESP_DATA_PREFIX):
                    line_data = line[len(OPENAI_RESP_DATA_PREFIX):-1]
                    if line_data.strip() == OPENAI_RESP_DONE:
                        pass
                    else:
                        openai_obj = json.loads(line_data)
                        yield openai_obj
