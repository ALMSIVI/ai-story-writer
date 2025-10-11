from pydantic import BaseModel
from .model import LlmModel


class CreateStoryRequest(BaseModel):
    title: str
    model: LlmModel
    category: str | None = None
    template: str | None = None


class CreateChapterRequest(BaseModel):
    lore: str | None = None
    current_outline: str
    next_outline: str | None = None
    after: str | None = None
    model: LlmModel | None = None
