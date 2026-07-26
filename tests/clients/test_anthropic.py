from types import SimpleNamespace

from anthropic import omit
from pytest_mock import MockerFixture

from ai_story_writer.clients import AnthropicClient
from ai_story_writer.types import LlmModel, Message, Role


def test_init(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    anthropic = mocker.patch('ai_story_writer.clients.anthropic.Anthropic', return_value=sdk_client)

    client = AnthropicClient(
        api_key='secret',
        supported_models={'model'},
        provider='Compatible',
        base_url='https://example.test',
    )

    anthropic.assert_called_once_with(api_key='secret', base_url='https://example.test')
    assert client.provider == 'Compatible'
    assert client.supported_models == {'model'}


def test_list_models_with_supported_models(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.list.return_value = [
        SimpleNamespace(id='supported'),
        SimpleNamespace(id='unsupported'),
    ]
    mocker.patch('ai_story_writer.clients.anthropic.Anthropic', return_value=sdk_client)
    client = AnthropicClient(api_key='secret', supported_models={'supported'}, provider='Compatible')

    models = client.list_models()

    assert models == [LlmModel(provider='Compatible', name='supported')]
    assert client.supported_models == {'supported'}


def test_list_models_with_empty_supported_models(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.list.return_value = [SimpleNamespace(id='one'), SimpleNamespace(id='two')]
    mocker.patch('ai_story_writer.clients.anthropic.Anthropic', return_value=sdk_client)
    client = AnthropicClient(api_key='secret', supported_models=set())

    models = client.list_models()

    assert models == [
        LlmModel(provider='Anthropic', name='one'),
        LlmModel(provider='Anthropic', name='two'),
    ]
    assert client.supported_models == {'one', 'two'}


def test_generate(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    stream = SimpleNamespace(text_stream=['First', ' second'])
    stream_context = mocker.MagicMock()
    stream_context.__enter__.return_value = stream
    sdk_client.messages.stream.return_value = stream_context
    mocker.patch('ai_story_writer.clients.anthropic.Anthropic', return_value=sdk_client)
    client = AnthropicClient(api_key='secret', supported_models={'model'})
    messages = [
        Message(role=Role.SYSTEM, content='System'),
        Message(role=Role.USER, content='Outline'),
    ]

    chunks = list(client.generate(messages, 'model'))

    assert chunks == ['First', ' second']
    sdk_client.messages.stream.assert_called_once_with(
        max_tokens=5000,
        system='System',
        messages=[
            {'role': Role.USER, 'content': 'Outline'},
        ],
        model='model',
    )


def test_generate_with_no_system_message(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    stream_context = mocker.MagicMock()
    stream_context.__enter__.return_value = SimpleNamespace(text_stream=[])
    sdk_client.messages.stream.return_value = stream_context
    mocker.patch('ai_story_writer.clients.anthropic.Anthropic', return_value=sdk_client)
    client = AnthropicClient(api_key='secret', supported_models={'model'})

    list(client.generate([Message(role=Role.USER, content='Outline')], 'model'))

    assert sdk_client.messages.stream.call_args.kwargs['system'] is omit


def test_close(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    mocker.patch('ai_story_writer.clients.anthropic.Anthropic', return_value=sdk_client)

    AnthropicClient(api_key='secret', supported_models={'model'}).close()

    sdk_client.close.assert_called_once_with()
