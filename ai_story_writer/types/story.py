from pydantic import BaseModel
from .model import LlmModel


class Story(BaseModel):
    id: str | None
    title: str
    model: LlmModel
    category: str | None
    template: str | None
