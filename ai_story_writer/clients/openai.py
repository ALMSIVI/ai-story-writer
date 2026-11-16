from openai import APIStatusError, OpenAI
from openai.types.responses import ResponseInputItemParam
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types import LlmModel


class OpenAIClient(LlmClient):
    __client: OpenAI

    def __init__(
        self,
        *,
        api_key: str | None = None,
        supported_models: set[str],
        provider: str = 'OpenAI',
        base_url: str | None = None,
    ):
        client_api_key = api_key
        if client_api_key is None and base_url is not None:
            # The OpenAI SDK requires a value even when the compatible local service does not use authentication.
            client_api_key = 'not-needed'

        self.__client = OpenAI(api_key=client_api_key, base_url=base_url)
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
        with self.__client.responses.stream(input=messages, model=model) as stream:
            for event in stream:
                if event.type == 'response.output_text.delta':
                    yield event.delta

    def count_input_tokens(self, prompt: str, model: str) -> int | None:
        messages = self.__create_input(prompt)
        try:
            response = self.__client.responses.input_tokens.count(
                input=messages,
                model=model,
            )
        except APIStatusError as error:
            # Compatible providers may support generation without the token-count endpoint.
            if error.status_code in {404, 405, 501}:
                return None
            raise
        return response.input_tokens

    @staticmethod
    def __create_input(prompt: str) -> list[ResponseInputItemParam]:
        return [{'role': 'user', 'content': prompt}]

    def close(self):
        self.__client.close()
