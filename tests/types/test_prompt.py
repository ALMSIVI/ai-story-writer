import pytest
from pydantic import ValidationError

from ai_story_writer.types import PromptSection, PromptTemplate


def test_prompt_template_defaults_sections_to_enabled():
    template = PromptTemplate.model_validate({'sections': [{'name': 'story-lore'}]})

    assert template.sections == [PromptSection(name='story-lore', enabled=True)]


@pytest.mark.parametrize(
    ('document', 'message'),
    [
        ({'sections': []}, 'at least 1 item'),
        ({'sections': [{'name': 'lore'}, {'name': 'lore'}]}, 'section names must be unique'),
        ({'sections': [{'name': 'lore', 'enabled': False}]}, 'at least one section must be enabled'),
        ({'sections': [{'name': 'lore', 'unexpected': True}]}, 'Extra inputs are not permitted'),
        ({'sections': [{'name': 'lore'}], 'unexpected': True}, 'Extra inputs are not permitted'),
    ],
)
def test_prompt_template_validation(document: dict, message: str):
    with pytest.raises(ValidationError, match=message):
        PromptTemplate.model_validate(document)
