from pydantic import BaseModel
from .model import LlmModel


class AddChapterRequest(BaseModel):
    current_outline: str
    next_outline: str | None = None
    after: str | None = None
    model: LlmModel | None = None


class UpdateChapterRequest(BaseModel):
    regenerate: bool
    outline: str | None = None
    lore: str | None = None
    content: str | None = None
    model: LlmModel | None = None
