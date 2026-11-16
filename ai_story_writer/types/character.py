from pydantic import BaseModel, ConfigDict


class Character(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str
    keywords: list[str] | None = None
    content: str
