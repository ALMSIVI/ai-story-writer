from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    api_key: str = Field(alias='apiKey')
    base_url: str | None = Field(default=None, alias='baseURL')
    included_models: list[str] | None = Field(default=None, alias='includedModels')
