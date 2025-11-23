from ollama import Client
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types import Message, LlmModel


class OllamaClient(LlmClient):
    __client: Client

    def __init__(
        self,
        *,
        api_key: str | None = None,
        supported_models: set[str],
        provider: str = 'Ollama',
        base_url: str | None = 'https://ollama.com',
    ):
        self.provider = provider
        if api_key is None:
            self.__client = Client()
        else:
            self.__client = Client(
                host=base_url,
                headers={'Authorization': f'Bearer {api_key}'},
            )
        self.supported_models = supported_models

    def list_models(self) -> list[LlmModel]:
        models = self.__client.list()
        model_names = [model.model for model in models.models if model.model is not None]
        if len(model_names) == 0:
            self.supported_models = set(model_names)

        return [
            LlmModel(provider=self.provider, name=model_name)
            for model_name in model_names
            if model_name in self.supported_models
        ]

    def generate(self, messages: list[Message], model: str) -> Iterator[str]:
        client_messages: list[dict[str, str]] = [{'role': message.role, 'content': message.content} for message in messages]
        for chunk in self.__client.chat(messages=client_messages, model=model, stream=True):
            yield chunk['message']['content']

    def close(self):
        pass  # Ollama client doesn't have a close() function
