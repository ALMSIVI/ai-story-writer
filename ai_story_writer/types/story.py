from pydantic import BaseModel, Field
from .model import LlmModel


class Story(BaseModel):
    id: str
    title: str
    model: LlmModel
    category: str | None = None
    template: str | None = None
    next_outline: str | None = Field(default=None, alias='nextOutline', serialization_alias='nextOutline')
    chapter_count: int | None = Field(default=None, alias='chapterCount', serialization_alias='chapterCount')
