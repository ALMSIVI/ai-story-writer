from anthropic import Anthropic
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types.model import LlmModel


class AnthropicClient(LlmClient):
    provider = 'Anthropic'
    __client: Anthropic

    def __init__(self, api_key: str, included_models: set[str]):
        self.__client = Anthropic(api_key=api_key)
        self.included_models = included_models

    def list_models(self) -> list[LlmModel]:
        models = self.__client.models.list()
        model_names = [model.id for model in models]
        if len(self.included_models) > 0:
            return [
                {'provider': self.provider, 'name': model_name}
                for model_name in model_names
                if model_name in self.included_models
            ]

    def generate(self, prompt: str, model: str) -> Iterator[str]:
        with self.__client.messages.stream(
            max_tokens=5000, messages=[{'role': 'user', 'content': prompt}], model=model
        ) as stream:
            for text in stream.text_stream:
                yield text
