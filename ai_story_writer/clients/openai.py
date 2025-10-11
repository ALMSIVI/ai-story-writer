from openai import OpenAI
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types.model import LlmModel


class OpenAIClient(LlmClient):
    __client: OpenAI

    def __init__(self, api_key: str, included_models: set[str], provider: str = 'OpenAI', base_url: str | None = None):
        self.__client = OpenAI(api_key=api_key, base_url=base_url)
        self.provider = provider
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
        with self.__client.responses.stream(input=prompt, model=model) as stream:
            for event in stream:
                if event.type == 'response.output_text.delta':
                    yield event.delta
