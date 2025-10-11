from pydantic import BaseModel, Field
from .model import LlmModel


class CreateStoryRequest(BaseModel):
    title: str
    model: LlmModel
    category: str | None = None
    template: str | None = None


class CreateChapterRequest(BaseModel):
    lore: str | None = None
    current_outline: str = Field(alias='currentOutline')
    next_outline: str | None = Field(default=None, alias='nextOutline')
    after: str | None = None
    model: LlmModel | None = None
