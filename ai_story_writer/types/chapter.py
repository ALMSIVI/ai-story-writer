from pydantic import BaseModel, model_validator
from typing import Any


class Chapter(BaseModel):
    id: str | None = None
    outline: str
    title: str | None = None
    content: str | None = None
    lore: str | None = None

    @model_validator(mode='before')
    @classmethod
    def extract_title(cls, data: Any) -> Any:
        if isinstance(data, dict):  
            content = data.get('content')
            if isinstance(content, str):
                lines = [line for line in content.splitlines()]
                if lines and lines[0].startswith('# '):
                    data['title'] = lines[0][2:].strip()
                    data['content'] = '\n'.join(lines[1:]).lstrip()

        return data

    @property
    def full_content(self) -> str:
        if self.content is None:
            raise ValueError('chapter content is missing')
        if self.title is None:
            return self.content

        return '# ' + self.title + '\n\n' + self.content

    @property
    def full_outline(self) -> str:
        if self.title is None:
            return self.outline

        return '# ' + self.title + '\n\n' + self.outline
