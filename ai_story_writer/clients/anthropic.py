from anthropic import Anthropic
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types import Message, LlmModel, Role


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
                LlmModel(provider=self.provider, name=model_name)
                for model_name in model_names
                if model_name in self.included_models
            ]
        return []

    def generate(self, messages: list[Message], model: str) -> Iterator[str]:
        system_message = next(message.content for message in messages if message.role == Role.SYSTEM)
        client_messages: list[dict[str, str]] = [
            {'role': message.role, 'content': message.content} for message in messages if message.role != Role.SYSTEM
        ]
        with self.__client.messages.stream(
            max_tokens=5000, system=system_message, messages=client_messages, model=model
        ) as stream:
            for text in stream.text_stream:
                yield text

    def close(self):
        self.__client.close()
