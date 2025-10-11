from google import genai
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types.model import LlmModel


class GoogleClient(LlmClient):
    provider = 'Google'
    __client: genai.Client

    def __init__(self, api_key: str, included_models: set[str]):
        self.__client = genai.Client(api_key=api_key)
        self.included_models = included_models

    def list_models(self) -> list[LlmModel]:
        models = self.__client.models.list()
        model_names = [model.name for model in models]
        if len(self.included_models) > 0:
            return [
                {'provider': self.provider, 'name': model_name}
                for model_name in model_names
                if model_name in self.included_models
            ]

    def generate(self, prompt: str, model: str) -> Iterator[str]:
        for chunk in self.__client.models.generate_content_stream(contents=prompt, model=model):
            yield chunk.text
