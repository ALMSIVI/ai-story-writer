from pydantic import BaseModel, Field

from ai_story_writer.types.chapter import Chapter


class GenerationEvent(BaseModel):
    event_type: str = Field(frozen=True, exclude=True)


class StartGenerationEvent(GenerationEvent):
    event_type: str = 'start'
    id: str


class GenerationInProgressEvent(GenerationEvent):
    event_type: str = 'in_progress'
    chunk: str


class GenerationCompletedEvent(GenerationEvent):
    event_type: str = 'complete'
    interrupted: bool
    content: str | None = None
    chapter: Chapter | None = None


class GenerationErrorEvent(GenerationEvent):
    event_type: str = 'error'
    message: str
