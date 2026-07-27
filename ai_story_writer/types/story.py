from pydantic import BaseModel

from .chapter import Chapter


class Story(BaseModel):
    id: str | None = None
    title: str
    style: str | None = None
    chapters: list[Chapter]
