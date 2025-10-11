from abc import ABC, abstractmethod
from typing import Iterator
from ai_story_writer.types.model import LlmModel


class LlmClient(ABC):
    provider: str
    included_models: set[str]

    @abstractmethod
    def list_models(self) -> list[LlmModel]:
        pass

    @abstractmethod
    def generate(self, prompt: str, model: str) -> Iterator[str]:
        pass
