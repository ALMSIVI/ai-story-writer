import pytest
from pydantic import ValidationError

from ai_story_writer.types import GenerationConfig, ModelConfig


def test_generation_config_accepts_camel_case_aliases():
    config = GenerationConfig.model_validate(
        {
            'model': 'OpenAI.gpt-5',
            'templates': {'write': 'default'},
            'fullChapterCount': 2,
        }
    )

    assert config.model == 'OpenAI.gpt-5'
    assert config.templates == {'write': 'default'}
    assert config.full_chapter_count == 2


def test_generation_config_rejects_negative_full_chapter_count():
    with pytest.raises(ValidationError, match='greater than or equal to 0'):
        GenerationConfig.model_validate({'fullChapterCount': -1})


def test_model_config_accepts_camel_case_aliases():
    config = ModelConfig.model_validate(
        {
            'apiKey': 'secret',
            'baseSdk': 'Anthropic',
            'baseUrl': 'https://example.test',
            'supportedModels': ['one', 'two'],
        }
    )

    assert config.api_key == 'secret'
    assert config.base_sdk == 'Anthropic'
    assert config.base_url == 'https://example.test'
    assert config.supported_models == ['one', 'two']


def test_model_config_defaults():
    config = ModelConfig()

    assert config.api_key is None
    assert config.base_sdk == 'OpenAI'
    assert config.base_url is None
    assert config.supported_models is None
