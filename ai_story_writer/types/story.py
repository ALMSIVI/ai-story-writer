from pydantic import BaseModel, Field
from .model import LlmModel


class Story(BaseModel):
    id: str
    title: str
    model: LlmModel
    category: str | None = None
    template: str | None = None
    style: str | None = None
    next_outline: str | None = Field(default=None, alias='nextOutline', serialization_alias='nextOutline')
    chapter_count: int | None = Field(
        default=None,
        alias='chapterCount',
        serialization_alias='chapterCount',
        description='Number of full chapters to include before using summaries.',
    )
    include_full_convo: bool = Field(
        default=False,
        alias='includeFullConvo',
        serialization_alias='includeFullConvo',
        description='Whether to include the full conversation for the generation.',
    )
