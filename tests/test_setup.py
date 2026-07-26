from pathlib import Path

from pytest import MonkeyPatch
from pytest_mock import MockerFixture
from ai_story_writer import setup


def test_initialize_clients(
    tmp_path: Path, monkeypatch: MonkeyPatch, mocker: MockerFixture
):
    config_directory = tmp_path / 'config'
    config_directory.mkdir()
    (config_directory / 'models.json').write_text(
        '{"Provider":{"apiKey":"key","baseSdk":"OpenAI","supportedModels":["model"]}}'
    )
    monkeypatch.chdir(tmp_path)
    add_client = mocker.patch.object(setup, 'add_client')

    setup.initialize_clients()

    add_client.assert_called_once()
    provider, config = add_client.call_args.args
    assert provider == 'Provider'
    assert config.api_key == 'key'
    assert config.supported_models == ['model']


def test_setup_and_teardown(mocker: MockerFixture):
    initialize_clients = mocker.patch.object(setup, 'initialize_clients')
    cleanup_clients = mocker.patch.object(setup, 'cleanup_clients')

    setup.setup()
    setup.teardown()

    initialize_clients.assert_called_once_with()
    cleanup_clients.assert_called_once_with()
