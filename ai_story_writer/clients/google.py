from google import genai
from google.genai import types
from typing import Iterator
from .__llm_client__ import LlmClient
from ai_story_writer.types import LlmModel


class GoogleClient(LlmClient):
    provider = 'Google'
    __client: genai.Client

    def __init__(self, *, api_key: str, supported_models: set[str]):
        self.__client = genai.Client(api_key=api_key)
        self.supported_models = supported_models

    def list_models(self) -> list[LlmModel]:
        models = self.__client.models.list()
        model_names = [model.name for model in models if model.name is not None]
        if len(self.supported_models) == 0:
            self.supported_models = set(model_names)

        return [
            LlmModel(provider=self.provider, name=model_name)
            for model_name in model_names
            if model_name in self.supported_models
        ]

    def generate(self, prompt: str, model: str) -> Iterator[str]:
        contents = self.__create_input(prompt)
        for chunk in self.__client.models.generate_content_stream(contents=contents, model=model):
            if chunk.prompt_feedback:
                raise RuntimeError(f'Message blocked: {chunk.prompt_feedback.block_reason}')

            if chunk.text is None:
                for candidate in chunk.candidates:
                    if candidate.finish_reason:
                        raise RuntimeError(f'Message blocked: {candidate.finish_reason}')

            yield chunk.text

    def count_input_tokens(self, prompt: str, model: str) -> int | None:
        contents = self.__create_input(prompt)
        response = self.__client.models.count_tokens(contents=contents, model=model)
        return response.total_tokens

    @staticmethod
    def __create_input(prompt: str):
        return [
            types.Content(
                role='user',
                parts=[types.Part.from_text(text=prompt)],
            )
        ]

    def close(self):
        self.__client.close()
