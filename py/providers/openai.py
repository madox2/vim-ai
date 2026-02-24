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

    default_options_varname_chat = "g:vim_ai_openai_chat"
    default_options_varname_complete = "g:vim_ai_openai_complete"
    default_options_varname_edit = "g:vim_ai_openai_edit"
    default_options_varname_image = "g:vim_ai_openai_image"

    def __init__(self, command_type: AICommandType, raw_options: Mapping[str, str], utils: AIUtils) -> None:
        self.utils = utils
        self.command_type = command_type
        config_varname = getattr(self, f"default_options_varname_{command_type}")
        raw_default_options = vim.eval(config_varname)
        self.options = self._parse_raw_options({**raw_default_options, **raw_options})

    def _protocol_type_check(self) -> None:
        # dummy method, just to ensure type safety
        utils: AIUtils
        options: Mapping[str, str] = {}
        provider: AIProvider = OpenAIProvider('chat', options, utils)

    def request(self, messages: Sequence[AIMessage]) -> Iterator[AIResponseChunk]:
        options = self.options
        is_responses = self._is_responses_endpoint(options['endpoint_url'])
        openai_options = self._make_responses_options(options) if is_responses else self._make_openai_options(options)
        http_options = {
            'request_timeout': options.get('request_timeout') or 20,
            'auth_type': options['auth_type'],
            'token_file_path': options['token_file_path'],
            'token_load_fn': options['token_load_fn'],
        }

        def _flatten_content(messages):
            # NOTE: Some providers like api.deepseek.com & api.groq.com expect a flat 'content' field.
            flattened = []
            for message in messages:
                message = {**message}
                if message['role'] in ('system', 'assistant'):
                    message['content'] = '\n'.join(map(lambda c: c['text'], message['content']))
                flattened.append(message)
            return flattened

        url = options['endpoint_url']

        if is_responses:
            request = {
                'input': self._make_responses_input(messages),
                **openai_options
            }
            self.utils.print_debug("openai: [{}] request: {}", self.command_type, request)
            response = self._openai_request(url, request, http_options)
            return self._responses_chunks(response, openai_options)

        request = {
            'messages': _flatten_content(messages),
            **openai_options
        }
        self.utils.print_debug("openai: [{}] request: {}", self.command_type, request)
        response = self._openai_request(url, request, http_options)
        return self._chat_completions_chunks(response, openai_options)

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

        def _convert_option(name, converter):
            if name in options and isinstance(options[name], str) and options[name] != '':
                try:
                    options[name] = converter(options[name])
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    raise self.utils.make_known_error(f"Invalid value for option '{name}': {options[name]}. Error: {e}")

        _convert_option('request_timeout', float)

        if self.command_type != 'image':
            _convert_option('stream', lambda x: bool(int(x)))
            _convert_option('max_tokens', int)
            _convert_option('max_completion_tokens', int)
            _convert_option('max_output_tokens', int)
            _convert_option('temperature', float)
            _convert_option('frequency_penalty', float)
            _convert_option('presence_penalty', float)
            _convert_option('top_p', float)
            _convert_option('seed', int)
            _convert_option('top_logprobs', int)
            _convert_option('logprobs', lambda x: bool(int(x)))
            _convert_option('stop', json.loads)
            _convert_option('logit_bias', json.loads)
            # reasoning_effort is a string, no conversion needed

            # openrouter reasoning parameter: https://openrouter.ai/docs/use-cases/reasoning-tokens#controlling-reasoning-tokens
            _convert_option('reasoning', json.loads)

        return options

    def _make_openai_options(self, options):
        result = {
            'model': options['model'],
        }

        option_keys = [
            'stream',
            'temperature',
            'max_tokens',
            'max_completion_tokens',
            'web_search_options',
            'frequency_penalty',
            'logit_bias',
            'logprobs',
            'presence_penalty',
            'reasoning_effort',
            'seed',
            'stop',
            'top_logprobs',
            'top_p',
            'reasoning', # openrouter reasoning parameter
        ]

        for key in option_keys:
            if key not in options:
                continue

            value = options[key]

            if value == '':
                continue

            # Backward compatibility: before using empty string "", values below
            # were used to exclude these params from the request
            if key == 'temperature' and value == -1:
                continue
            if key == 'max_tokens' and value == 0:
                continue
            if key == 'max_completion_tokens' and value == 0:
                continue

            result[key] = value

        return result

    def _make_responses_options(self, options):
        result = {
            'model': options['model'],
        }

        option_keys = [
            'stream',
            'temperature',
            'top_p',
            'seed',
            'stop',
            'reasoning',
        ]

        for key in option_keys:
            if key not in options:
                continue

            value = options[key]
            if value == '':
                continue

            result[key] = value

        max_output_tokens = options.get('max_output_tokens')
        if max_output_tokens in ('', None, 0):
            max_completion_tokens = options.get('max_completion_tokens')
            if max_completion_tokens not in ('', None, 0):
                max_output_tokens = max_completion_tokens
            else:
                max_tokens = options.get('max_tokens')
                if max_tokens not in ('', None, 0):
                    max_output_tokens = max_tokens

        if max_output_tokens not in ('', None, 0):
            result['max_output_tokens'] = max_output_tokens

        if 'reasoning' not in result:
            reasoning_effort = options.get('reasoning_effort')
            if reasoning_effort not in ('', None):
                result['reasoning'] = { 'effort': reasoning_effort }

        return result

    def _make_responses_input(self, messages: Sequence[AIMessage]):
        input_items = []
        for message in messages:
            role = message.get('role')
            content = message.get('content') or []
            if not content:
                input_items.append({
                    'type': 'message',
                    'role': role,
                    'content': "",
                })
                continue
            response_content = []
            for part in content:
                if part.get('type') == 'text':
                    response_content.append({
                        'type': 'input_text',
                        'text': part.get('text', ''),
                    })
                elif part.get('type') == 'image_url':
                    image_url = part.get('image_url', {})
                    if image_url.get('url'):
                        response_content.append({
                            'type': 'input_image',
                            'image_url': image_url.get('url'),
                        })
            input_items.append({
                'type': 'message',
                'role': role,
                'content': response_content if response_content else "",
            })
        return input_items

    def _responses_chunks(self, response: Iterator[Mapping[str, Any]], options: Mapping[str, Any]):
        if options.get('stream'):
            def _map_chunk(resp):
                return self._map_responses_stream_event(resp)
            return filter(lambda chunk: chunk is not None, map(_map_chunk, response))

        def _non_stream_chunks():
            resp = next(response, None)
            if resp is None:
                return
            chunk = self._map_responses_response(resp)
            if chunk is not None:
                yield chunk
        return _non_stream_chunks()

    def _map_responses_stream_event(self, resp: Mapping[str, Any]):
        self.utils.print_debug("openai: [{}] response: {}", self.command_type, resp)
        event_type = resp.get('type')

        if event_type == 'response.output_text.delta':
            delta = resp.get('delta') or ''
            return {'type': 'assistant', 'content': delta} if delta else None

        if event_type == 'response.content_part.added':
            part = resp.get('part') or {}
            text = part.get('text') or ''
            return {'type': 'assistant', 'content': text} if text else None

        if event_type == 'error':
            message = resp.get('message') or 'OpenAI Responses API error'
            raise Exception(message)

        return None

    def _map_responses_response(self, resp: Mapping[str, Any]):
        self.utils.print_debug("openai: [{}] response: {}", self.command_type, resp)
        if resp.get('error'):
            raise Exception(resp['error'])

        output_text = resp.get('output_text')
        if isinstance(output_text, str) and output_text:
            return {'type': 'assistant', 'content': output_text}

        output = resp.get('output') or []
        text_parts = []
        for item in output:
            if item.get('type') == 'message':
                for part in item.get('content', []):
                    if part.get('type') in ('output_text', 'text'):
                        text_parts.append(part.get('text', ''))
            elif item.get('type') == 'output_text':
                text_parts.append(item.get('text', ''))

        if text_parts:
            return {'type': 'assistant', 'content': ''.join(text_parts)}
        return None

    def _chat_completions_chunks(self, response, openai_options):
        _choice_key = 'delta' if openai_options.get('stream') else 'message'

        def _get_delta(resp):
            choices = resp.get('choices') or [{}]
            return choices[0].get(_choice_key, {})

        def _map_chunk(resp):
            self.utils.print_debug("openai: [{}] response: {}", self.command_type, resp)
            delta = _get_delta(resp)
            if delta.get('reasoning_content'):
                # NOTE: support for deepseek's reasoning_content
                return {'type': 'thinking', 'content': delta.get('reasoning_content')}
            if delta.get('reasoning'):
                # NOTE: support for `reasoning` from openrouter
                return {'type': 'thinking', 'content': delta.get('reasoning')}
            if delta.get('content'):
                return {'type': 'assistant', 'content': delta.get('content')}
            return None # invalid chunk, this occured in deepseek models

        def _filter_valid_chunks(chunk):
            return chunk is not None

        return filter(_filter_valid_chunks, map(_map_chunk, response))

    def _is_responses_endpoint(self, url: str) -> bool:
        return '/responses' in url

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

        proxy_settings = self.utils.get_proxy_settings()
        if proxy_settings:
            proxy_handler = urllib.request.ProxyHandler(proxy_settings)
            opener = urllib.request.build_opener(proxy_handler)
            response = opener.open(req, timeout=request_timeout)
        else:
            response = urllib.request.urlopen(req, timeout=request_timeout)

        with response:
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
