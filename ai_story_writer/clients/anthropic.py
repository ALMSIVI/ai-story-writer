from anthropic import Anthropic
from anthropic.types import MessageParam
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types import LlmModel


class AnthropicClient(LlmClient):
    provider = 'Anthropic'
    __client: Anthropic

    def __init__(
        self,
        *,
        api_key: str,
        supported_models: set[str],
        provider: str = 'Anthropic',
        base_url: str | None = None,
    ):
        self.__client = Anthropic(api_key=api_key, base_url=base_url)
        self.provider = provider
        self.supported_models = supported_models

    def list_models(self) -> list[LlmModel]:
        models = self.__client.models.list()
        model_names = [model.id for model in models]
        if len(self.supported_models) == 0:
            self.supported_models = set(model_names)

        return [
            LlmModel(provider=self.provider, name=model_name)
            for model_name in model_names
            if model_name in self.supported_models
        ]

    def generate(self, prompt: str, model: str) -> Iterator[str]:
        messages = self.__create_input(prompt)
        with self.__client.messages.stream(max_tokens=5000, messages=messages, model=model) as stream:
            for text in stream.text_stream:
                yield text

    def count_input_tokens(self, prompt: str, model: str) -> int:
        messages = self.__create_input(prompt)
        response = self.__client.messages.count_tokens(
            messages=messages,
            model=model,
        )
        return response.input_tokens

    @staticmethod
    def __create_input(prompt: str) -> list[MessageParam]:
        return [{'role': 'user', 'content': prompt}]

    def close(self):
        self.__client.close()
