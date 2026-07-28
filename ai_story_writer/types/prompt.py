from pydantic import BaseModel, ConfigDict, Field, model_validator


class PromptSection(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str
    enabled: bool = True


class PromptTemplate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    sections: list[PromptSection] = Field(min_length=1)

    @model_validator(mode='after')
    def validate_sections(self) -> 'PromptTemplate':
        names = [section.name for section in self.sections]
        if len(names) != len(set(names)):
            raise ValueError('section names must be unique')
        if not any(section.enabled for section in self.sections):
            raise ValueError('at least one section must be enabled')
        return self
