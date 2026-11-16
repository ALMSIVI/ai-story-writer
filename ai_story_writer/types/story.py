from .background import Background
from pydantic import BaseModel

from .chapter import Chapter
from .character import Character


class Story(BaseModel):
    id: str | None = None
    title: str
    style: str | None = None
    background: list[Background] | None = None
    instructions: list[str] | None = None
    characters: list[Character] | None = None
    chapters: list[Chapter]
