from collections.abc import Sequence, Mapping, Iterator
from typing import TypedDict, Literal, Union, List, Protocol, Tuple, Any

types_py_imported = True

# TODO: prefix types with AI
class TextContent(TypedDict):
    type: Literal['text']
    text: str

class ImageUrlContent(TypedDict):
    type: Literal['image_url']
    image_url: dict[str, str]  # {'url': str}

MessageContent = Union[TextContent, ImageUrlContent]

class Message(TypedDict):
    role: Literal['system', 'user', 'assistant']
    content: List[MessageContent]
    type: str

class AIUtils(Protocol):
    def print_debug(self, text: str, *args: Any):
        pass
    def make_known_error(self, message: str):
        pass
    def load_api_key(self, env_variable: str, file_path: str):
        pass

class ResponseChunk(TypedDict):
    type: Literal['content', 'thinking']
    content: str

class AIProvider(Protocol):
    def __init__(self, options: Mapping[str, str], utils: AIUtils) -> None:
        pass

    def request(self, messages: Sequence[Message]) -> Iterator[ResponseChunk]:
        pass
