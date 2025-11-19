from abc import ABC, abstractmethod
from typing import Iterator
from ai_story_writer.types import Message, LlmModel


class LlmClient(ABC):
    provider: str
    included_models: set[str]

    @abstractmethod
    def list_models(self) -> list[LlmModel]:
        pass

    @abstractmethod
    def generate(self, messages: list[Message], model: str) -> Iterator[str]:
        pass

    @abstractmethod
    def close(self):
        pass
