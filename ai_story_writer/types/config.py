from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    api_key: str = Field(alias='apiKey')
    base_sdk: str = Field(default='OpenAI', alias='baseSdk')
    base_url: str | None = Field(default=None, alias='baseUrl')
    supported_models: list[str] | None = Field(default=None, alias='supportedModels')
