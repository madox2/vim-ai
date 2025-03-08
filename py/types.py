from collections.abc import Sequence, Mapping, Iterator
from typing import TypedDict, Literal, Union, List, Protocol

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

class ResponseChunk(TypedDict):
    type: Literal['content', 'thinking']
    content: str

# TODO: how to properly extend this class
# TODO: how to provide helper functions (like logging, raising errors), maybe extending a base class
class AIProvider(Protocol):
    def __init__(self, config: Mapping[str, str]) -> None:
        pass

    def request(self, messages: Sequence[Message]) -> Iterator[ResponseChunk]:
        pass

