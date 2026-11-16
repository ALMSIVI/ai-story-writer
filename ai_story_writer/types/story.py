from .background import Background
from pydantic import BaseModel

from .chapter import Chapter


class Story(BaseModel):
    id: str | None = None
    title: str
    style: str | None = None
    background: list[Background] | None = None
    chapters: list[Chapter]
