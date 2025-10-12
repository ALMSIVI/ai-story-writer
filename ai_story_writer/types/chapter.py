from pydantic import BaseModel
from .model import LlmModel


class Chapter(BaseModel):
    id: str
    outline: str
    content: str
    lore: str | None = None
    model: LlmModel | None = None
