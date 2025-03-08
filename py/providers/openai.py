from collections.abc import Sequence, Mapping, Iterator
import urllib.request

if False:
    from py.utils import print_debug
    from py.types import Message, ResponseChunk

# TODO: each provider should provide it's error handling
# TODO: each provider should take care of it's default options
# TODO: how to properly extend AIProvider from types.py
# TODO: expose helper utils e.g. load api key
class OpenAIProvider():

    def __init__(self, options: Mapping[str, str]) -> None:
        self.options = options

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
        print_debug("[engine-chat] request: {}", request)
        url = options['endpoint_url']
        response = self._openai_request(url, request, http_options)

        def _choices(resp):
            choices = resp.get('choices', [{}])

            # NOTE choices may exist in the response, but be an empty list.
            if not choices:
                return [{}]

            return choices

        def map_chunk_no_stream(resp) -> ResponseChunk:
            print_debug("[engine-chat] response: {}", resp)
            content = _choices(resp)[0].get('message', {}).get('content', '')
            return {'type': 'content', 'content': content}

        def map_chunk_stream(resp) -> ResponseChunk:
            print_debug("[engine-chat] response: {}", resp)
            content = _choices(resp)[0].get('delta', {}).get('content', '')
            return {'type': 'content', 'content': content}

        map_chunk = map_chunk_stream if openai_options['stream'] else map_chunk_no_stream

        return map(map_chunk, response)

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
            (OPENAI_API_KEY, OPENAI_ORG_ID) = load_api_key(options['token_file_path'])
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
