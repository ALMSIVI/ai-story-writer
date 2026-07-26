from types import SimpleNamespace

from pytest_mock import MockerFixture

from ai_story_writer.clients import OllamaClient
from ai_story_writer.types import LlmModel, Message, Role


def test_init(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    ollama_client = mocker.patch('ai_story_writer.clients.ollama.Client', return_value=sdk_client)

    client = OllamaClient(supported_models={'model'})

    ollama_client.assert_called_once_with()
    assert client.provider == 'Ollama'
    assert client.supported_models == {'model'}


def test_init_with_api_key(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    ollama_client = mocker.patch('ai_story_writer.clients.ollama.Client', return_value=sdk_client)

    client = OllamaClient(
        api_key='secret',
        supported_models={'model'},
        provider='Compatible',
        base_url='https://example.test',
    )

    ollama_client.assert_called_once_with(
        host='https://example.test',
        headers={'Authorization': 'Bearer secret'},
    )
    assert client.provider == 'Compatible'


def test_list_models_with_supported_models(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.list.return_value = SimpleNamespace(
        models=[
            SimpleNamespace(model='supported'),
            SimpleNamespace(model='unsupported'),
            SimpleNamespace(model=None),
        ]
    )
    mocker.patch('ai_story_writer.clients.ollama.Client', return_value=sdk_client)
    client = OllamaClient(supported_models={'supported'})

    models = client.list_models()

    assert models == [LlmModel(provider='Ollama', name='supported')]
    assert client.supported_models == {'supported'}


def test_list_models_with_empty_supported_models(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.list.return_value = SimpleNamespace(models=[SimpleNamespace(model='one'), SimpleNamespace(model='two')])
    mocker.patch('ai_story_writer.clients.ollama.Client', return_value=sdk_client)
    client = OllamaClient(supported_models=set())

    models = client.list_models()

    assert models == [
        LlmModel(provider='Ollama', name='one'),
        LlmModel(provider='Ollama', name='two'),
    ]
    assert client.supported_models == {'one', 'two'}


def test_generate(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.chat.return_value = [
        {'message': {'content': 'First'}},
        {'message': {'content': ' second'}},
    ]
    mocker.patch('ai_story_writer.clients.ollama.Client', return_value=sdk_client)
    client = OllamaClient(supported_models={'model'})
    messages = [
        Message(role=Role.SYSTEM, content='System'),
        Message(role=Role.USER, content='Outline'),
    ]

    chunks = list(client.generate(messages, 'model'))

    assert chunks == ['First', ' second']
    sdk_client.chat.assert_called_once_with(
        messages=[
            {'role': Role.SYSTEM, 'content': 'System'},
            {'role': Role.USER, 'content': 'Outline'},
        ],
        model='model',
        stream=True,
    )


def test_count_input_tokens(mocker: MockerFixture):
    mocker.patch('ai_story_writer.clients.ollama.Client')
    client = OllamaClient(supported_models={'model'})

    input_tokens = client.count_input_tokens([Message(role=Role.USER, content='Outline')], 'model')

    assert input_tokens is None
