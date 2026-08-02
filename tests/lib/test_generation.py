import pytest
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from ai_story_writer.lib import generation
from ai_story_writer.lib.config import GenerationConfigError
from ai_story_writer.types import (
    GenerationCompletedEvent,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
)


def test_dry_run_without_model(
    mocker: MockerFixture,
    capsys: CaptureFixture[str],
):
    initialize_clients = mocker.patch.object(generation, 'initialize_clients')
    cleanup_clients = mocker.patch.object(generation, 'cleanup_clients')
    apply_completion = mocker.Mock()

    generation.run_generation(
        'Prompt',
        None,
        apply_completion,
        dry_run=True,
    )

    assert capsys.readouterr().out == 'Prompt\n'
    apply_completion.assert_not_called()
    initialize_clients.assert_not_called()
    cleanup_clients.assert_not_called()


def test_dry_run_with_model(
    mocker: MockerFixture,
    capsys: CaptureFixture[str],
):
    model = LlmModel(provider='Provider', name='model')
    mocker.patch.object(generation, 'initialize_clients')
    count_input_tokens = mocker.patch.object(generation, 'count_input_tokens', return_value=123)
    cleanup_clients = mocker.patch.object(generation, 'cleanup_clients')
    apply_completion = mocker.Mock()

    generation.run_generation('Prompt', model, apply_completion, dry_run=True)

    assert capsys.readouterr().out == 'Prompt\nInput tokens: 123\n'
    count_input_tokens.assert_called_once_with('Prompt', model)
    apply_completion.assert_not_called()
    cleanup_clients.assert_called_once_with()


def test_dry_run_without_token_count(
    mocker: MockerFixture,
    capsys: CaptureFixture[str],
):
    prompt = 'Prompt'
    model = LlmModel(provider='Ollama', name='model')
    mocker.patch.object(generation, 'initialize_clients')
    count_input_tokens = mocker.patch.object(generation, 'count_input_tokens', return_value=None)
    cleanup_clients = mocker.patch.object(generation, 'cleanup_clients')
    apply_completion = mocker.Mock()

    generation.run_generation(prompt, model, apply_completion, dry_run=True)

    assert capsys.readouterr().out == 'Prompt\n'
    count_input_tokens.assert_called_once_with(prompt, model)
    apply_completion.assert_not_called()
    cleanup_clients.assert_called_once_with()


def test_run_generation_requires_model(mocker: MockerFixture):
    initialize_clients = mocker.patch.object(generation, 'initialize_clients')

    with pytest.raises(GenerationConfigError, match='No model configured'):
        generation.run_generation(
            'Prompt',
            None,
            mocker.Mock(),
        )

    initialize_clients.assert_not_called()


def test_run_generation(mocker: MockerFixture, capsys: CaptureFixture[str]):
    prompt = 'Prompt'
    model = LlmModel(provider='Provider', name='model')
    completed = GenerationCompletedEvent(content='Content')
    initialize_clients = mocker.patch.object(generation, 'initialize_clients')
    generate = mocker.patch.object(
        generation,
        'generate',
        return_value=[
            GenerationInProgressEvent(chunk='First '),
            GenerationInProgressEvent(chunk='second'),
            completed,
        ],
    )
    cleanup_clients = mocker.patch.object(generation, 'cleanup_clients')
    apply_completion = mocker.Mock()

    generation.run_generation(prompt, model, apply_completion)

    assert capsys.readouterr().out == 'First second'
    initialize_clients.assert_called_once_with()
    generate.assert_called_once_with(prompt, model)
    apply_completion.assert_called_once_with(completed)
    cleanup_clients.assert_called_once_with()


def test_run_generation_error_event(mocker: MockerFixture, capsys: CaptureFixture[str]):
    prompt = 'Prompt'
    model = LlmModel(provider='Provider', name='model')
    mocker.patch.object(generation, 'initialize_clients')
    mocker.patch.object(
        generation,
        'generate',
        return_value=[GenerationErrorEvent(message='provider failed')],
    )
    cleanup_clients = mocker.patch.object(generation, 'cleanup_clients')
    apply_completion = mocker.Mock()

    generation.run_generation(prompt, model, apply_completion)

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == 'Encountered error provider failed\n'
    apply_completion.assert_not_called()
    cleanup_clients.assert_called_once_with()


def test_generation_lifecycle_cleans_up_on_exception(mocker: MockerFixture):
    error = RuntimeError('failed')
    mocker.patch.object(generation, 'initialize_clients')
    mocker.patch.object(generation, 'generate', side_effect=error)
    cleanup_clients = mocker.patch.object(generation, 'cleanup_clients')

    with pytest.raises(RuntimeError, match='failed'):
        generation.run_generation(
            'Prompt',
            LlmModel(provider='Provider', name='model'),
            mocker.Mock(),
        )

    cleanup_clients.assert_called_once_with()
