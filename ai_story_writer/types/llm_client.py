from pydantic import BaseModel
from enum import Enum

class Role(str, Enum):
    SYSTEM = 'system',
    ASSISTANT = 'assistant',
    USER = 'user'


class Message(BaseModel):
    role: Role
    content: str
