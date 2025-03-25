from collections.abc import Sequence, Mapping, Iterator
from typing import Any
import urllib.request
import os
import json
import vim

if "VIMAI_DUMMY_IMPORT" in os.environ:
    # TODO: figure out how to properly use imports/modules in vim, dev environment, pytest
    from py.types import AIMessage, AIResponseChunk, AIUtils, AIProvider, AICommandType, AIImageResponseChunk

class OpenAIProvider():

    def __init__(self, command_type: AICommandType, raw_options: Mapping[str, str], utils: AIUtils) -> None:
        self.utils = utils
        self.command_type = command_type
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
            'auth_type': options['auth_type'],
            'token_file_path': options['token_file_path'],
            'token_load_fn': options['token_load_fn'],
        }

        def _flatten_content(messages):
            # NOTE: Some providers like api.deepseek.com & api.groq.com expect a flat 'content' field.
            for message in messages:
                match message['role']:
                    case 'system' | 'assistant':
                        message['content'] = '\n'.join(map(lambda c: c['text'], message['content']))
            return messages

        request = {
            'messages': _flatten_content(messages),
            **openai_options
        }
        self.utils.print_debug("openai: [{}] request: {}", self.command_type, request)
        url = options['endpoint_url']
        response = self._openai_request(url, request, http_options)

        _choice_key = 'delta' if openai_options['stream'] else 'message'

        def _get_delta(resp):
            choices = resp.get('choices') or [{}]
            return choices[0].get(_choice_key, {})

        def _map_chunk(resp):
            self.utils.print_debug("openai: [{}] response: {}", self.command_type, resp)
            delta = _get_delta(resp)
            if delta.get('reasoning_content'):
                # NOTE: support for deepseek's reasoning_content
                return {'type': 'thinking', 'content': delta.get('reasoning_content')}
            if delta.get('content'):
                return {'type': 'assistant', 'content': delta.get('content')}
            return None # invalid chunk, this occured in deepseek models

        def _filter_valid_chunks(chunk):
            return chunk is not None

        return filter(_filter_valid_chunks, map(_map_chunk, response))

    def _load_api_key(self):
        raw_api_key = self.utils.load_api_key(
            "OPENAI_API_KEY",
            token_file_path=self.options['token_file_path'],
            token_load_fn=self.options['token_load_fn'],
        )
        # The text is in format of "<api key>,<org id>" and the
        # <org id> part is optional
        elements = raw_api_key.strip().split(",")
        api_key = elements[0].strip()
        org_id = None

        if len(elements) > 1:
            org_id = elements[1].strip()

        return (api_key, org_id)

    def _parse_raw_options(self, raw_options: Mapping[str, Any]):
        if raw_options.get('enable_auth', 1) == "0":
            # raise error for users who don't use default value of this obsolete option
            raise self.utils.make_known_error("`enable_auth = 0` option is no longer supported. use `auth_type = none` instead")

        options = {**raw_options}
        options['request_timeout'] = float(options['request_timeout'])
        if self.command_type != 'image':
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
            'stream': options['stream'],
        }
        if options['temperature'] > -1:
            result['temperature'] = options['temperature']

        if max_tokens > 0:
            result['max_tokens'] = max_tokens
        if max_completion_tokens > 0:
            result['max_completion_tokens'] = max_completion_tokens
        return result

    def request_image(self, prompt: str) -> list[AIImageResponseChunk]:
        options = self.options
        http_options = {
            'request_timeout': options['request_timeout'],
            'auth_type': options['auth_type'],
            'token_file_path': options['token_file_path'],
            'token_load_fn': options['token_load_fn'],
        }
        openai_options = {
            'model': options['model'],
            'quality': options['quality'],
            'size': options['size'],
            'style': options['style'],
            'response_format': 'b64_json',
        }
        request = { 'prompt': prompt, **openai_options }
        self.utils.print_debug("openai: [{}] request: {}", self.command_type, request)
        url = options['endpoint_url']
        response, *_ = self._openai_request(url, request, http_options)
        self.utils.print_debug("openai: [{}] response: {}", self.command_type, { 'images_count': len(response['data']) })
        b64_data = response['data'][0]['b64_json']
        return [{ 'b64_data': b64_data }]

    def _openai_request(self, url, data, options):
        RESP_DATA_PREFIX = 'data: '
        RESP_DONE = '[DONE]'

        auth_type = options['auth_type']
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VimAI",
        }

        if auth_type == 'bearer':
            (OPENAI_API_KEY, OPENAI_ORG_ID) = self._load_api_key()
            headers['Authorization'] = f"Bearer {OPENAI_API_KEY}"

            if OPENAI_ORG_ID is not None:
                headers["OpenAI-Organization"] =  f"{OPENAI_ORG_ID}"

        if auth_type == 'api-key':
            (OPENAI_API_KEY, _) = self._load_api_key()
            headers['api-key'] = f"{OPENAI_API_KEY}"

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
                if line.startswith(RESP_DATA_PREFIX):
                    line_data = line[len(RESP_DATA_PREFIX):-1]
                    if line_data.strip() == RESP_DONE:
                        pass
                    else:
                        openai_obj = json.loads(line_data)
                        yield openai_obj
