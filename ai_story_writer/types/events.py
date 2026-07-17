from pydantic import BaseModel


class GenerationEvent(BaseModel):
    pass


class GenerationInProgressEvent(GenerationEvent):
    chunk: str


class GenerationCompletedEvent(GenerationEvent):
    content: str


class GenerationErrorEvent(GenerationEvent):
    message: str
