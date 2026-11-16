from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class Background(BaseModel):
    model_config = ConfigDict(extra='forbid')

    content: str
    keywords: list[str] | None = None

    @model_validator(mode='before')
    @classmethod
    def normalize_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {'content': data}
        return data
