from pydantic import BaseModel
from .model import LlmModel


class Story(BaseModel):
    id: str | None = None
    title: str
    model: LlmModel
    category: str | None = None
    template: str | None = None
    next_outline: str | None = None
