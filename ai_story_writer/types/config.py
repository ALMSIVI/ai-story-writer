from pydantic import BaseModel


class ModelConfig(BaseModel):
    api_key: str
    base_url: str | None
    included_models: list[str] | None
