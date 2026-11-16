import pytest
from pydantic import ValidationError

from ai_story_writer.types import Background


@pytest.mark.parametrize('value', ['General facts', {'content': 'General facts', 'keywords': None}])
def test_background_normalizes_unconditional_entries(value: str | dict):
    background = Background.model_validate(value)

    assert background.content == 'General facts'
    assert background.keywords is None


def test_background_preserves_empty_keywords():
    assert Background(content='Details', keywords=[]).keywords == []


@pytest.mark.parametrize('value', [123, {'keywords': ['gate']}, {'content': 123}])
def test_background_rejects_invalid_content(value):
    with pytest.raises(ValidationError):
        Background.model_validate(value)
