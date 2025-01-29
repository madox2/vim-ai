from collections.abc import Sequence, Mapping
from typing import TypedDict, Protocol


class AIProvider(Protocol):

  def __init__(self, config: Mapping[str, str]) -> None:
      pass

  def request(self, messages: Sequence[Message]) -> Generator[str]:
      pass

class Message(TypedDict):
    role: str
    content: str
    type: str

