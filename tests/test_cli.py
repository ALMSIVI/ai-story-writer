import pytest
from pytest_mock import MockerFixture

from ai_story_writer import cli
from ai_story_writer.commands import CommandError
from ai_story_writer.commands.generate import generate
from ai_story_writer.lib.prompt import PromptTemplateError


def test_generate_command_is_registered():
    args = cli.parser.parse_args(['generate', 'story.yaml', '--dry-run'])

    assert args.command == 'generate'
    assert args.file == 'story.yaml'
    assert args.dry_run is True
    assert args.func is generate


@pytest.mark.parametrize('error', [CommandError('failed'), PromptTemplateError('failed')])
def test_start_converts_known_errors(mocker: MockerFixture, error: ValueError):
    command = mocker.Mock(side_effect=error)
    mocker.patch.object(cli.parser, 'parse_args', return_value=mocker.Mock(func=command))
    parser_error = mocker.patch.object(cli.parser, 'error', side_effect=SystemExit(2))

    with pytest.raises(SystemExit, match='2'):
        cli.start()

    parser_error.assert_called_once_with('failed')
