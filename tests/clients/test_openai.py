from types import SimpleNamespace

from openai import omit
from pytest_mock import MockerFixture

from ai_story_writer.clients import OpenAIClient
from ai_story_writer.types import LlmModel, Message, Role


def test_init(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    openai = mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)

    client = OpenAIClient(
        api_key='secret',
        supported_models={'model'},
        provider='Compatible',
        base_url='https://example.test',
    )

    openai.assert_called_once_with(api_key='secret', base_url='https://example.test')
    assert client.provider == 'Compatible'
    assert client.supported_models == {'model'}


def test_init_without_api_key(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    openai = mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)

    OpenAIClient(
        supported_models={'model'},
        provider='Local',
        base_url='http://localhost:1234/v1',
    )

    openai.assert_called_once_with(api_key='not-needed', base_url='http://localhost:1234/v1')


def test_list_models_with_supported_models(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.list.return_value = [
        SimpleNamespace(id='supported'),
        SimpleNamespace(id='unsupported'),
    ]
    mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)
    client = OpenAIClient(api_key='secret', supported_models={'supported'}, provider='Compatible')

    models = client.list_models()

    assert models == [LlmModel(provider='Compatible', name='supported')]
    assert client.supported_models == {'supported'}


def test_list_models_with_empty_supported_models(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.list.return_value = [SimpleNamespace(id='one'), SimpleNamespace(id='two')]
    mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)
    client = OpenAIClient(api_key='secret', supported_models=set())

    models = client.list_models()

    assert models == [
        LlmModel(provider='OpenAI', name='one'),
        LlmModel(provider='OpenAI', name='two'),
    ]
    assert client.supported_models == {'one', 'two'}


def test_generate(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    stream_context = mocker.MagicMock()
    stream_context.__enter__.return_value = [
        SimpleNamespace(type='response.created'),
        SimpleNamespace(type='response.output_text.delta', delta='First'),
        SimpleNamespace(type='response.output_text.delta', delta=' second'),
    ]
    sdk_client.responses.stream.return_value = stream_context
    mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)
    client = OpenAIClient(api_key='secret', supported_models={'model'})
    messages = [
        Message(role=Role.SYSTEM, content='System'),
        Message(role=Role.USER, content='Outline'),
    ]

    chunks = list(client.generate(messages, 'model'))

    assert chunks == ['First', ' second']
    sdk_client.responses.stream.assert_called_once_with(
        instructions='System',
        input=[
            {'role': Role.USER, 'content': 'Outline'},
        ],
        model='model',
    )


def test_generate_with_no_system_message(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    stream_context = mocker.MagicMock()
    stream_context.__enter__.return_value = []
    sdk_client.responses.stream.return_value = stream_context
    mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)
    client = OpenAIClient(api_key='secret', supported_models={'model'})

    list(client.generate([Message(role=Role.USER, content='Question')], 'model'))

    assert sdk_client.responses.stream.call_args.kwargs['instructions'] is omit


def test_close(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)

    OpenAIClient(api_key='secret', supported_models={'model'}).close()

    sdk_client.close.assert_called_once_with()
