from pydantic import BaseModel


class WebUiMessage(BaseModel):
    id: str
    content: str
    model: str | None = None


class WebUiHistory(BaseModel):
    messages: dict[str, WebUiMessage]


class WebUiChat(BaseModel):
    models: list[str]
    history: WebUiHistory
    messages: list[WebUiMessage]


class WebUiChat(BaseModel):
    id: str
    title: str
    chat: WebUiChat
