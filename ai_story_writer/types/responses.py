from pydantic import BaseModel, Field
from ai_story_writer.types.chapter import Chapter


class GenerationEvent(BaseModel):
    event_type: str = Field(frozen=True, exclude=True)


class GenerationStartedEvent(GenerationEvent):
    event_type: str = 'start'
    id: str


class GenerationInProgressEvent(GenerationEvent):
    event_type: str = 'in_progress'
    chunk: str


class GenerationCompletedEvent(GenerationEvent):
    event_type: str = 'complete'
    interrupted: bool
    content: str | Chapter = None


class GenerationErrorEvent(GenerationEvent):
    event_type: str = 'error'
    message: str
