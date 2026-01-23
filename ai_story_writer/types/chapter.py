from pydantic import BaseModel, model_validator
from typing import Any
from .model import LlmModel


class Chapter(BaseModel):
    id: str
    outline: str
    title: str | None = None
    content: str
    lore: str | None = None
    model: LlmModel | None = None

    @model_validator(mode='before')
    @classmethod
    def extract_title(cls, data: Any) -> Any:
        if isinstance(data, dict):  
            content = data.get('content')
            if isinstance(content, str):
                lines = [line for line in content.splitlines() if line.strip() != '']
                if lines and lines[0].startswith('# '):
                    data['title'] = lines[0][2:].strip()
                    data['content'] = '\n\n'.join(lines[1:]).lstrip()

        return data

    @property
    def full_content(self):
        if self.title is None:
            return self.content

        return '# ' + self.title + '\n\n' + self.content

    @property
    def full_outline(self):
        if self.title is None:
            return self.outline

        return '# ' + self.title + '\n\n' + self.outline
