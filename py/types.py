from collections.abc import Sequence, Mapping
from typing import TypedDict, Literal, Union, List


class AIProvider(Protocol):

  def __init__(self, config: Mapping[str, str]) -> None:
      pass

  def request(self, messages: Sequence[Message]) -> Generator[str]:
      pass

class Message(TypedDict):
    role: str
    content: str
    type: str


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

