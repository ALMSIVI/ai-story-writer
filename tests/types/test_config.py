from ai_story_writer.types import ModelConfig


def test_accepts_camel_case_aliases():
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


def test_defaults():
    config = ModelConfig()

    assert config.api_key is None
    assert config.base_sdk == 'OpenAI'
    assert config.base_url is None
    assert config.supported_models is None
