from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    model: str | None = None
    templates: dict[str, str] | None = None
    full_chapter_count: int | None = Field(default=None, ge=0, alias='fullChapterCount')


class ModelConfig(BaseModel):
    api_key: str | None = Field(default=None, alias='apiKey')
    base_sdk: str = Field(default='OpenAI', alias='baseSdk')
    base_url: str | None = Field(default=None, alias='baseUrl')
    supported_models: list[str] | None = Field(default=None, alias='supportedModels')
