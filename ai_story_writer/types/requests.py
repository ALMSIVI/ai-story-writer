from pydantic import BaseModel
from .model import LlmModel


class InsertChapterRequest(BaseModel):
    current_outline: str
    next_outline: str | None
    after: str | None
    model: LlmModel | None


class UpdateChapterRequest(BaseModel):
    regenerate: bool
    current_outline: str | None
    content: str | None
    model: LlmModel | None
