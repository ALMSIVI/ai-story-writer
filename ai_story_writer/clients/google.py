from google import genai
from google.genai import types
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types import Message, LlmModel, Role


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
                LlmModel(provider=self.provider, name=model_name)
                for model_name in model_names
                if model_name in self.included_models
            ]
        return []

    def generate(self, messages: list[Message], model: str) -> Iterator[str]:
        try:
            config = types.GenerateContentConfig(
                system_instruction=next(message.content for message in messages if message.role == Role.SYSTEM)
            )
        except StopIteration:
            config = None

        contents = [
            types.Content(
                role='user' if message.role == Role.USER else 'model',
                parts=[types.Part.from_text(text=message.content)],
            )
            for message in messages
            if message.role != Role.SYSTEM
        ]

        for chunk in self.__client.models.generate_content_stream(contents=contents, model=model, config=config):
            yield chunk.text

    def close(self):
        self.__client.close()
