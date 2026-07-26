import pytest

from ai_story_writer.types import LlmModel


@pytest.mark.parametrize(
    ('value', 'provider', 'name'),
    [('OpenAI.gpt-5', 'OpenAI', 'gpt-5'), ('Google.gemini-3.1-pro', 'Google', 'gemini-3.1-pro')],
)
def test_parse(value: str, provider: str, name: str):
    assert LlmModel.parse(value) == LlmModel(provider=provider, name=name)


def test_parse_rejects_invalid_value():
    with pytest.raises(ValueError, match='Failed to parse model invalid'):
        LlmModel.parse('invalid')
