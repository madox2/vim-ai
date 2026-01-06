from collections.abc import Sequence, Mapping, Iterator
from typing import TypedDict, Literal, Union, List, Protocol, Tuple, Any

types_py_imported = True

class AITextContent(TypedDict):
    type: Literal['text']
    text: str

class AIImageUrlContent(TypedDict):
    type: Literal['image_url']
    image_url: dict[str, str]  # {'url': str}

AIMessageContent = Union[AITextContent, AIImageUrlContent]

class AIMessage(TypedDict):
    role: Literal['system', 'user', 'assistant', 'tool']
    content: List[AIMessageContent]

class AIUtils(Protocol):
    def print_debug(self, text: str, *args: Any):
        pass
    def make_known_error(self, message: str):
        pass
    def load_api_key(self, env_variable: str, token_file_path: str = "", token_load_fn: str = ""):
        pass
    def get_proxy_settings(self):
        pass

class AIResponseChunk(TypedDict):
    type: Literal['assistant', 'thinking']
    content: str

class AIImageResponseChunk(TypedDict):
    b64_data: str

AICommandType = Literal['chat', 'edit', 'complete', 'image']

class AIProvider(Protocol):

    # optional config variable names (used to populate all options)
    default_options_varname_chat: str = ""
    default_options_varname_complete: str = ""
    default_options_varname_edit: str = ""

    def __init__(self, command_type: AICommandType, raw_options: Mapping[str, str], utils: AIUtils) -> None:
        pass

    def request(self, messages: Sequence[AIMessage]) -> Iterator[AIResponseChunk]:
        pass

    def request_image(self, prompt: str) -> list[AIImageResponseChunk]:
        pass
