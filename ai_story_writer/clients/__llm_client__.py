from abc import ABC, abstractmethod
from typing import Iterator
from ai_story_writer.types import LlmModel


class LlmClient(ABC):
    provider: str
    supported_models: set[str]

    @abstractmethod
    def list_models(self) -> list[LlmModel]:
        pass

    @abstractmethod
    def generate(self, prompt: str, model: str) -> Iterator[str]:
        pass

    @abstractmethod
    def count_input_tokens(self, prompt: str, model: str) -> int | None:
        pass

    @abstractmethod
    def close(self):
        pass
