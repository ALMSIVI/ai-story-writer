from pydantic import BaseModel
from .model import LlmModel


class Chapter(BaseModel):
    id: str | None
    outline: str
    content: str | None
    lore: str | None
    model: LlmModel | None
