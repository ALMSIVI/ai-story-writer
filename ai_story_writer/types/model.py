from pydantic import BaseModel


class LlmModel(BaseModel):
    provider: str
    name: str
