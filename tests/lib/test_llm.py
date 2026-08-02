import json
import pytest
from pathlib import Path
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from ai_story_writer.lib import llm
from ai_story_writer.types import (
    GenerationCompletedEvent,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
)
from tests.conftest import MockClient


def test_initialize_clients(tmp_path: Path, monkeypatch: MonkeyPatch, mocker: MockerFixture):
    models = {
        'Anthropic': {'apiKey': 'key', 'supportedModels': ['model']},
        'Google': {'apiKey': 'key', 'supportedModels': ['model']},
        'Ollama': {'apiKey': 'key', 'supportedModels': ['model'], 'base_url': 'https://test'},
        'CustomAnthropic': {
            'baseSdk': 'Anthropic',
            'baseUrl': 'https://test',
            'apiKey': 'key',
            'supportedModels': ['model'],
        },
        'CustomOpenAI': {
            'baseSdk': 'OpenAI',
            'baseUrl': 'https://test',
            'apiKey': 'key',
            'supportedModels': ['model'],
        },
    }

    config_directory = tmp_path / 'config'
    config_directory.mkdir()
    (config_directory / 'models.json').write_text(json.dumps(models))
    monkeypatch.chdir(tmp_path)

    llm.initialize_clients()

    assert len(llm.clients) == 5
    for provider, client in llm.clients.items():
        assert client.provider == provider
        assert client.supported_models == set(models[provider]['supportedModels'])


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

    input_tokens = llm.count_input_tokens('Prompt', LlmModel(provider='test', name='model'))

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
        llm.count_input_tokens('Prompt', model)


def test_generate():
    client = MockClient(chunks=['First ', 'second'])
    llm.clients['test'] = client
    model = LlmModel(provider='test', name='model')

    events = list(llm.generate('Prompt', model))

    assert events == [
        GenerationInProgressEvent(chunk='First '),
        GenerationInProgressEvent(chunk='second'),
        GenerationCompletedEvent(content='First second'),
    ]
    assert len(client.calls) == 1
    generated_messages, model_name = client.calls[0]
    assert model_name == 'model'
    assert generated_messages == 'Prompt'


def test_generate_error():
    client = MockClient(error=RuntimeError('provider failed'))
    llm.clients['test'] = client

    events = list(
        llm.generate(
            'Prompt',
            LlmModel(provider='test', name='model'),
        )
    )

    assert events == [GenerationErrorEvent(message='provider failed')]


@pytest.mark.parametrize(
    ('model', 'message'),
    [
        (LlmModel(provider='missing', name='model'), 'client missing does not exist'),
        (LlmModel(provider='test', name='unsupported'), 'model unsupported not supported in client test'),
    ],
)
def test_generate_validates_model(model: LlmModel, message: str):
    llm.clients['test'] = MockClient()

    with pytest.raises(ValueError, match=message):
        list(llm.generate('Prompt', model))
