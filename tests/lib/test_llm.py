import pytest
from pytest_mock import MockerFixture

from ai_story_writer.lib import llm
from ai_story_writer.types import (
    GenerationCompletedEvent,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
    Message,
    ModelConfig,
    Role,
)
from tests.conftest import MockClient


@pytest.mark.parametrize(
    ('provider', 'base_sdk', 'client_name', 'expected_kwargs'),
    [
        ('Anthropic', 'OpenAI', 'AnthropicClient', {'api_key': 'key', 'supported_models': {'model'}}),
        ('Google', 'OpenAI', 'GoogleClient', {'api_key': 'key', 'supported_models': {'model'}}),
        (
            'Ollama',
            'OpenAI',
            'OllamaClient',
            {'api_key': 'key', 'supported_models': {'model'}, 'provider': 'Ollama', 'base_url': 'https://test'},
        ),
        (
            'CustomAnthropic',
            'Anthropic',
            'AnthropicClient',
            {
                'api_key': 'key',
                'supported_models': {'model'},
                'provider': 'CustomAnthropic',
                'base_url': 'https://test',
            },
        ),
        (
            'CustomOpenAI',
            'OpenAI',
            'OpenAIClient',
            {
                'api_key': 'key',
                'supported_models': {'model'},
                'provider': 'CustomOpenAI',
                'base_url': 'https://test',
            },
        ),
    ],
)
def test_add_client(
    provider: str,
    base_sdk: str,
    client_name: str,
    expected_kwargs: dict[str, object],
    mocker: MockerFixture,
):
    client = mocker.Mock()
    client_class = mocker.patch.object(llm, client_name, return_value=client)
    config = ModelConfig(
        apiKey='key',
        baseSdk=base_sdk,
        baseUrl='https://test',
        supportedModels=['model'],
    )

    llm.add_client(provider, config)

    assert llm.clients[provider] is client
    client_class.assert_called_once_with(**expected_kwargs)


def test_cleanup_clients():
    first = MockClient()
    second = MockClient()
    llm.clients.update({'first': first, 'second': second})

    llm.cleanup_clients()

    assert first.closed
    assert second.closed
    assert llm.clients == {}


def test_count_input_tokens():
    client = MockClient()
    llm.clients['test'] = client
    messages = [Message(role=Role.USER, content='Prompt')]

    input_tokens = llm.count_input_tokens(messages, LlmModel(provider='test', name='model'))

    assert input_tokens == 42


@pytest.mark.parametrize(
    ('model', 'message'),
    [
        (LlmModel(provider='missing', name='model'), 'client missing does not exist'),
        (LlmModel(provider='test', name='unsupported'), 'model unsupported not supported in client test'),
    ],
)
def test_count_input_tokens_validates_model(model: LlmModel, message: str):
    llm.clients['test'] = MockClient()

    with pytest.raises(ValueError, match=message):
        llm.count_input_tokens([Message(role=Role.USER, content='Prompt')], model)


def test_generate():
    client = MockClient(chunks=['First ', 'second'])
    llm.clients['test'] = client
    messages = [Message(role=Role.USER, content='Prompt')]
    model = LlmModel(provider='test', name='model')

    events = list(llm.generate(messages, model))

    assert events == [
        GenerationInProgressEvent(chunk='First '),
        GenerationInProgressEvent(chunk='second'),
        GenerationCompletedEvent(content='First second'),
    ]
    assert len(client.calls) == 1
    generated_messages, model_name = client.calls[0]
    assert model_name == 'model'
    assert generated_messages == messages


def test_generate_error():
    client = MockClient(error=RuntimeError('provider failed'))
    llm.clients['test'] = client

    events = list(
        llm.generate(
            [Message(role=Role.USER, content='Prompt')],
            LlmModel(provider='test', name='model'),
        )
    )

    assert events == [GenerationErrorEvent(message='provider failed')]


def test_generate_missing_client():
    with pytest.raises(ValueError, match='client missing does not exist'):
        list(
            llm.generate(
                [Message(role=Role.USER, content='Prompt')],
                LlmModel(provider='missing', name='model'),
            )
        )


def test_generate_unsupported_model():
    llm.clients['test'] = MockClient()

    with pytest.raises(ValueError, match='model unsupported not supported in client test'):
        list(
            llm.generate(
                [Message(role=Role.USER, content='Prompt')],
                LlmModel(provider='test', name='unsupported'),
            )
        )
