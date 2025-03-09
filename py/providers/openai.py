from collections.abc import Sequence, Mapping, Iterator
from typing import Any
import urllib.request
import os
import vim

if "VIMAI_DUMMY_IMPORT" in os.environ:
    # TODO: figure out how to properly use imports/modules in vim, dev environment, pytest
    from py.types import AIMessage, AIResponseChunk, AIUtils, AIProvider, AICommandType

class OpenAIProvider():

    def __init__(self, command_type: AICommandType, raw_options: Mapping[str, str], utils: AIUtils) -> None:
        self.utils = utils
        raw_default_options = vim.eval(f"g:vim_ai_openai_{command_type}")
        self.options = self._parse_raw_options({**raw_default_options, **raw_options})

    def _protocol_type_check(self) -> None:
        # dummy method, just to ensure type safety
        utils: AIUtils
        options: Mapping[str, str] = {}
        provider: AIProvider = OpenAIProvider('chat', options, utils)

    def request(self, messages: Sequence[AIMessage]) -> Iterator[AIResponseChunk]:
        options = self.options
        openai_options = self._make_openai_options(options)
        http_options = {
            'request_timeout': options['request_timeout'],
            'enable_auth': options['enable_auth'],
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

        def map_chunk_no_stream(resp) -> AIResponseChunk:
            self.utils.print_debug("[engine-chat] response: {}", resp)
            content = _choices(resp)[0].get('message', {}).get('content', '')
            return {'type': 'assistant', 'content': content}

        def map_chunk_stream(resp) -> AIResponseChunk:
            self.utils.print_debug("[engine-chat] response: {}", resp)
            content = _choices(resp)[0].get('delta', {}).get('content', '')
            return {'type': 'assistant', 'content': content}

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

    def _parse_raw_options(self, raw_options: Mapping[str, Any]):
        options = {**raw_options}
        options['request_timeout'] = float(options['request_timeout'])
        options['enable_auth'] = bool(int(options['enable_auth']))
        options['max_tokens'] = int(options['max_tokens'])
        options['max_completion_tokens'] = int(options['max_completion_tokens'])
        options['temperature'] = float(options['temperature'])
        options['stream'] = bool(int(options['stream']))
        return options

    def _make_openai_options(self, options):
        max_tokens = options['max_tokens']
        max_completion_tokens = options['max_completion_tokens']
        result = {
            'model': options['model'],
            'temperature': options['temperature'],
            'stream': options['stream'],
        }
        if max_tokens > 0:
            result['max_tokens'] = max_tokens
        if max_completion_tokens > 0:
            result['max_completion_tokens'] = max_completion_tokens
        return result

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
