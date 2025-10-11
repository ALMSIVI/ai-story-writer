from pydantic import BaseModel
from .model import LlmModel


class Chapter(BaseModel):
    id: str | None = None
    outline: str
    content: str | None = None
    lore: str | None = None
    model: LlmModel | None = None
