import pytest
from pytest_mock import MockerFixture

from ai_story_writer import cli
from ai_story_writer.commands import CommandError
from ai_story_writer.commands.write import write
from ai_story_writer.lib.prompt import PromptTemplateError


def test_write_command_is_registered():
    args = cli.parser.parse_args(['write', 'story.yaml', '--dry-run'])

    assert args.command == 'write'
    assert args.file == 'story.yaml'
    assert args.dry_run is True
    assert args.func is write


@pytest.mark.parametrize('error', [CommandError('failed'), PromptTemplateError('failed')])
def test_start_converts_known_errors(mocker: MockerFixture, error: ValueError):
    command = mocker.Mock(side_effect=error)
    mocker.patch.object(cli.parser, 'parse_args', return_value=mocker.Mock(func=command))
    parser_error = mocker.patch.object(cli.parser, 'error', side_effect=SystemExit(2))

    with pytest.raises(SystemExit, match='2'):
        cli.start()

    parser_error.assert_called_once_with('failed')
