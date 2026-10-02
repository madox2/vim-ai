import logging
import tempfile
from collections.abc import Sequence, Mapping, Iterator
from pathlib import Path
from typing import TypedDict, Literal, Union, List, Protocol, Any

import openai
from openai import Stream
from openai.types.responses import ResponseInputParam, Response, ResponseStreamEvent


class AITextContent(TypedDict):
    type: Literal['text']
    text: str


class AIImageUrlContent(TypedDict):
    type: Literal['image_url']
    image_url: dict[str, str]  # {'url': str}


AIMessageContent = Union[AITextContent, AIImageUrlContent]


class AIMessage(TypedDict):
    role: Literal['system', 'user', 'assistant', 'developer']
    content: List[AIMessageContent]


class AIUtils(Protocol):
    def print_debug(self, text: str, *args: Any):
        pass

    def make_known_error(self, message: str):
        pass

    def load_api_key(self, env_variable: str, token_file_path: str = "", token_load_fn: str = ""):
        pass


class AIResponseChunk(TypedDict):
    type: Literal['assistant', 'thinking']
    content: str


class AIImageResponseChunk(TypedDict):
    b64_data: str


AICommandType = Literal['chat', 'edit', 'complete', 'image']


class AIProvider(Protocol):
    def __init__(self, command_type: AICommandType, raw_options: Mapping[str, str], utils: AIUtils) -> None:
        pass

    def request(self, messages: Sequence[AIMessage]) -> Iterator[AIResponseChunk]:
        pass

    def request_image(self, prompt: str) -> list[AIImageResponseChunk]:
        pass

class LoggingConfiguration:

    PLUGIN_DEFAULT_FILE = Path(tempfile.gettempdir()) / "vim-ai-openai-responses.log"
    OPENAI_DEFAULT_FILE = Path(tempfile.gettempdir()) / "vim-ai-openai-responses-ai.log"

    def __init__(self, enabled: bool = False, file: Path = None):
        self.enabled: bool = enabled
        self.file: Path = file

class OpenAiResponsesProvider:
    """
    OpenAiResponsesProvider backed by the OpenAI python package.
    """

    def __init__(self, command_type: AICommandType,
                 raw_options: Mapping[str, str],
                 utils: AIUtils,
                 under_test: bool = False,
                 logging_configuration: LoggingConfiguration = None,
                 logging_ai_configuration: LoggingConfiguration = None,
                 ) -> None:
        self.utils = utils
        self.command_type = command_type
        self._set_options(raw_options, under_test)
        self._set_loggers(logging_configuration, logging_ai_configuration, under_test)

    def request(self, messages: Sequence[AIMessage]) -> Iterator[AIResponseChunk]:
        """
        Example: https://github.com/openai/openai-python/blob/main/examples/streaming.py
        """
        self.logger_plugin.debug("Prompting with: %s", messages)
        open_ai_messages = [self._map_to_response_input_param(m) for m in messages]
        if self._initial_prompt_enabled() and not self._initial_prompt_already_included(open_ai_messages):
            open_ai_messages = [self._make_initial_prompt_message()] + open_ai_messages
        self.logger_open_ai.debug("Prompting with: %s", open_ai_messages)
        self.logger_plugin.debug("Options: %s", self.options)
        openai_response = openai.responses.create(
            input=open_ai_messages,
            model=self.options['model'],
            stream=bool(self.options['stream']),
            tools=self.options.get('tools', []),
            tool_choice=self.options.get('tool_choice', 'auto'))
    stream=bool(self.options['stream']),
        if not self.options['stream']:
            self.logger_open_ai.debug('Non-streaming response...')
            openai_response: Response
            response_type = openai_response.output[0].role
            response_text = openai_response.output[0].content[0].text
            response_chunk_type = response_type if response_type == "assistant" else "thinking"
            chunk = {
                "type": response_chunk_type,
                "content": response_text,
            }
            self.logger_open_ai.debug(openai_response)
            self.logger_plugin.debug(chunk)
            yield chunk
        if self.options['stream']:
            self.logger_open_ai.debug('Streaming response...')
            openai_response: Stream[ResponseStreamEvent]
            for response_event in openai_response:
                if response_event.type == 'response.content_part.added':
                    chunk = {
                        "type": "assistant",
                        "content": response_event.part.text,
                    }
                    self.logger_open_ai.debug(response_event.type + ": " + chunk['content'])
                    self.logger_plugin.debug(chunk)
                    yield chunk
                elif response_event.type == 'response.output_text.delta':
                    chunk = {
                        "type": "assistant",
                        "content": response_event.delta,
                    }
                    self.logger_open_ai.debug(response_event.type + ": " + chunk['content'])
                    self.logger_plugin.debug(chunk)
                    yield chunk
                elif response_event.type == 'response.completed':
                    self.logger_open_ai.debug(response_event.type)
                    return
                elif response_event.type == 'error':
                    e = Exception(f"Error (code: {response_event.code}) - {response_event.message}")
                    self.logger_plugin.exception(e)
                    raise e
                else:
                    self.logger_open_ai.debug(response_event.type)
                    continue
                    # Expected events, which may or may not need to be handled.
                    # {
                    #     'response.content_part.done',
                    #     'response.created',
                    #     'response.failed',
                    #     'response.file_search_call.completed',
                    #     'response.file_search_call.in_progress',
                    #     'response.file_search_call.searching',
                    #     'response.function_call_arguments.delta',
                    #     'response.function_call_arguments.done',
                    #     'response.in_progress',
                    #     'response.incomplete',
                    #     'response.output_item.added',
                    #     'response.output_item.done',
                    #     'response.output_text.annotation.added',
                    #     'response.output_text.done',
                    #     'response.reasoning_summary_part.added',
                    #     'response.reasoning_summary_part.done',
                    #     'response.reasoning_summary_text.delta',
                    #     'response.reasoning_summary_text.done',
                    #     'response.refusal.delta',
                    #     'response.refusal.done',
                    #     'response.web_search_call.completed',
                    #     'response.web_search_call.in_progress',
                    #     'response.web_search_call.searching',
                    # }

    def _map_to_response_input_param(self, message: AIMessage) -> ResponseInputParam:
        if not message['content']:
            return {
                'content': "",
                'role': message['role'],
                'type': 'message',
            }

        first_content_element = message['content'][0]
        if isinstance(first_content_element, str):
            return {
                'content': first_content_element,
                'role': message['role'],
                'type': 'message',
            }
        elif isinstance(first_content_element, dict):
            content = first_content_element['image_url'] \
                if 'image_url' in first_content_element.keys() \
                else first_content_element['text']
            return {
                'content': content,
                'role': message['role'],
                'type': 'message',
            }
        else:
            raise Exception(f"Handling of `{first_content_element.__class__.__name__}` messages not implemented.")

    def _initial_prompt_enabled(self) -> bool:
        return bool(self.options['initial_prompt'])

    def _initial_prompt_already_included(self, open_ai_messages):
        messages_contents = set(m['content'].strip() for m in open_ai_messages)
        initial_prompt = self._make_initial_prompt_message()
        return initial_prompt['content'] in messages_contents

    def _make_initial_prompt_message(self) -> dict:
        return {
                'content': self.options.get('initial_prompt', '').strip(),
                'role': 'user',
                'type': 'message',
        }

    def _set_options(self, raw_options: Mapping[str, str], under_test: bool = False) -> None:
        self.options = raw_options or {}
        self.options['initial_prompt'] = self._set_options_initial_prompt(raw_options)
        self.options['stream'] = self._coerce_to_bool(self.options['stream']) \
            if 'stream' in self.options \
            else False
        self.options['stream'] = bool(self.options['stream'])
        if not under_test:
            import vim
            self.options = self.options | vim.eval(f"g:vim_ai_openai_responses_config") or {}
        for key, value in self.options.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                self.options[key] = float(value)

    def _set_options_initial_prompt(self, raw_options: dict):
        if 'initial_prompt' not in raw_options:
            return None
        if isinstance(raw_options['initial_prompt'], str):
            return raw_options['initial_prompt'].strip()
        if isinstance(raw_options['initial_prompt'], list):
            return '\n'.join(raw_options['initial_prompt']).strip()

    def _coerce_to_bool(self, value: str) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip().lower() in ['true', '1', 't', 'y', 'yes']
        return bool(value)

    def _protocol_type_check(self) -> None:
        # dummy method, just to ensure type safety
        utils: AIUtils
        options: Mapping[str, str] = {}
        provider: AIProvider = OpenAiResponsesProvider('chat', options, utils)

    def _set_loggers(self,
                     logging_configuration: LoggingConfiguration,
                     logging_ai_configuration: LoggingConfiguration,
                     under_test: bool) -> None:
        enable_logging = False
        enable_logging_ai = False

        if under_test:
            enable_logging = logging_configuration.enabled
            logging_file = logging_configuration.file
            enable_logging_ai = logging_ai_configuration.enabled
            logging_ai_file = logging_ai_configuration.file
            if enable_logging:
                self.logging_file = logging_file
                if self.logging_file and not self.logging_file.exists():
                    self.logging_file.parent.mkdir(parents=True, exist_ok=True)
                    self.logging_file.touch()
            if enable_logging_ai:
                self.logging_file_openai = logging_ai_file
                if self.logging_file_openai and not self.logging_file_openai.exists():
                    self.logging_file_openai.parent.mkdir(parents=True, exist_ok=True)
                    self.logging_file_openai.touch()

        if not under_test:
            # Vim configuration is used.
            import vim
            enable_logging = self._coerce_to_bool(vim.eval(f"g:vim_ai_openai_responses_logging"))
            enable_ai_logging = self._coerce_to_bool(vim.eval(f"g:vim_ai_openai_responses_ai_logging"))
            if enable_logging:
                self.logging_file = Path(vim.eval(f"g:vim_ai_openai_responses_logging_file") or LoggingConfiguration.PLUGIN_DEFAULT_FILE)
                if self.logging_file and not self.logging_file.exists():
                    self.logging_file.parent.mkdir(parents=True, exist_ok=True)
                    self.logging_file.touch()
            if enable_ai_logging:
                self.logging_file_openai = Path(vim.eval(f"g:vim_ai_openai_responses_ai_logging_file") or LoggingConfiguration.OPENAI_DEFAULT_FILE)
                if self.logging_file and not self.logging_file.exists():
                    self.logging_file_openai.parent.mkdir(parents=True, exist_ok=True)
                    self.logging_file_openai.touch()

        if enable_logging:
            self.logger_plugin = self._create_logger("vim-ai-provider-openai-logger", self.logging_file)
        else:
            self.logger_plugin = self._create_noop_logger("vim-ai-provider-openai-logger")
        if enable_logging_ai:
            self.logger_open_ai = self._create_logger("open-ai-responses-logger", self.logging_file_openai)
        else:
            self.logger_open_ai = self._create_noop_logger("open-ai-responses-logger")

    def _create_logger(self, logger_name: str, logging_file: Path):
        assert logger_name
        if not logging_file:
            return self._create_noop_logger(logger_name)
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(logging_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def _create_noop_logger(self, logger_name: str):
        noop_logger = logging.getLogger(logger_name)
        noop_logger.addHandler(logging.NullHandler())
        return noop_logger

