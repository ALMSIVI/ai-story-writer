from types import SimpleNamespace

from pytest_mock import MockerFixture

from ai_story_writer.clients import AnthropicClient
from ai_story_writer.types import LlmModel


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
    prompt = 'Outline'

    chunks = list(client.generate(prompt, 'model'))

    assert chunks == ['First', ' second']
    sdk_client.messages.stream.assert_called_once_with(
        max_tokens=5000,
        messages=[
            {'role': 'user', 'content': prompt},
        ],
        model='model',
    )


def test_count_input_tokens(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.messages.count_tokens.return_value = SimpleNamespace(input_tokens=42)
    mocker.patch('ai_story_writer.clients.anthropic.Anthropic', return_value=sdk_client)
    client = AnthropicClient(api_key='secret', supported_models={'model'})
    prompt = 'Outline'

    input_tokens = client.count_input_tokens(prompt, 'model')

    assert input_tokens == 42
    sdk_client.messages.count_tokens.assert_called_once_with(
        messages=[{'role': 'user', 'content': prompt}],
        model='model',
    )


def test_close(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    mocker.patch('ai_story_writer.clients.anthropic.Anthropic', return_value=sdk_client)

    AnthropicClient(api_key='secret', supported_models={'model'}).close()

    sdk_client.close.assert_called_once_with()
