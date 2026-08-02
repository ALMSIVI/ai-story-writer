from types import SimpleNamespace

from pytest_mock import MockerFixture

from ai_story_writer.clients import OpenAIClient
from ai_story_writer.types import LlmModel


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
    prompt = 'Outline'

    chunks = list(client.generate(prompt, 'model'))

    assert chunks == ['First', ' second']
    sdk_client.responses.stream.assert_called_once_with(
        input=[
            {'role': 'user', 'content': prompt},
        ],
        model='model',
    )


def test_count_input_tokens(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.responses.input_tokens.count.return_value = SimpleNamespace(input_tokens=42)
    mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)
    client = OpenAIClient(api_key='secret', supported_models={'model'})
    prompt = 'Outline'

    input_tokens = client.count_input_tokens(prompt, 'model')

    assert input_tokens == 42
    sdk_client.responses.input_tokens.count.assert_called_once_with(
        input=[{'role': 'user', 'content': prompt}],
        model='model',
    )


def test_close(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    mocker.patch('ai_story_writer.clients.openai.OpenAI', return_value=sdk_client)

    OpenAIClient(api_key='secret', supported_models={'model'}).close()

    sdk_client.close.assert_called_once_with()
