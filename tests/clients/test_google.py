from types import SimpleNamespace

import pytest
from pytest_mock import MockerFixture

from ai_story_writer.clients import GoogleClient
from ai_story_writer.types import LlmModel, Message, Role


def test_init(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    google_client = mocker.patch('ai_story_writer.clients.google.genai.Client', return_value=sdk_client)

    client = GoogleClient(api_key='secret', supported_models={'model'})

    google_client.assert_called_once_with(api_key='secret')
    assert client.provider == 'Google'
    assert client.supported_models == {'model'}


def test_list_models_with_supported_models(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.list.return_value = [
        SimpleNamespace(name='supported'),
        SimpleNamespace(name='unsupported'),
        SimpleNamespace(name=None),
    ]
    mocker.patch('ai_story_writer.clients.google.genai.Client', return_value=sdk_client)
    client = GoogleClient(api_key='secret', supported_models={'supported'})

    models = client.list_models()

    assert models == [LlmModel(provider='Google', name='supported')]
    assert client.supported_models == {'supported'}


def test_list_models_with_empty_supported_models(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.list.return_value = [SimpleNamespace(name='one'), SimpleNamespace(name='two')]
    mocker.patch('ai_story_writer.clients.google.genai.Client', return_value=sdk_client)
    client = GoogleClient(api_key='secret', supported_models=set())

    models = client.list_models()

    assert models == [
        LlmModel(provider='Google', name='one'),
        LlmModel(provider='Google', name='two'),
    ]
    assert client.supported_models == {'one', 'two'}


def test_generate(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.generate_content_stream.return_value = [
        SimpleNamespace(prompt_feedback=None, text='First', candidates=[]),
        SimpleNamespace(prompt_feedback=None, text=' second', candidates=[]),
    ]
    mocker.patch('ai_story_writer.clients.google.genai.Client', return_value=sdk_client)
    client = GoogleClient(api_key='secret', supported_models={'model'})
    messages = [
        Message(role=Role.SYSTEM, content='System'),
        Message(role=Role.USER, content='Outline'),
    ]

    chunks = list(client.generate(messages, 'model'))

    assert chunks == ['First', ' second']
    call = sdk_client.models.generate_content_stream.call_args
    assert call.kwargs['model'] == 'model'
    assert call.kwargs['config'].system_instruction == 'System'
    contents = call.kwargs['contents']
    assert contents[0].role == 'user'
    assert contents[0].parts[0].text == 'Outline'


def test_generate_with_no_system_message(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.generate_content_stream.return_value = []
    mocker.patch('ai_story_writer.clients.google.genai.Client', return_value=sdk_client)
    client = GoogleClient(api_key='secret', supported_models={'model'})

    list(client.generate([Message(role=Role.USER, content='Outline')], 'model'))

    assert sdk_client.models.generate_content_stream.call_args.kwargs['config'] is None


def test_generate_raises_for_prompt_feedback(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.generate_content_stream.return_value = [
        SimpleNamespace(
            prompt_feedback=SimpleNamespace(block_reason='SAFETY'),
            text=None,
            candidates=[],
        )
    ]
    mocker.patch('ai_story_writer.clients.google.genai.Client', return_value=sdk_client)
    client = GoogleClient(api_key='secret', supported_models={'model'})

    with pytest.raises(RuntimeError, match='Message blocked: SAFETY'):
        list(client.generate([Message(role=Role.USER, content='Question')], 'model'))


def test_generate_raises_for_candidate_finish_reason(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    sdk_client.models.generate_content_stream.return_value = [
        SimpleNamespace(
            prompt_feedback=None,
            text=None,
            candidates=[SimpleNamespace(finish_reason='RECITATION')],
        )
    ]
    mocker.patch('ai_story_writer.clients.google.genai.Client', return_value=sdk_client)
    client = GoogleClient(api_key='secret', supported_models={'model'})

    with pytest.raises(RuntimeError, match='Message blocked: RECITATION'):
        list(client.generate([Message(role=Role.USER, content='Question')], 'model'))


def test_close(mocker: MockerFixture):
    sdk_client = mocker.Mock()
    mocker.patch('ai_story_writer.clients.google.genai.Client', return_value=sdk_client)

    GoogleClient(api_key='secret', supported_models={'model'}).close()

    sdk_client.close.assert_called_once_with()
