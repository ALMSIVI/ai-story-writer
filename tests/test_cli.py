from argparse import Namespace
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from ai_story_writer import cli
from ai_story_writer.types import (
    Chapter,
    GenerationCompletedEvent,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
    Message,
    Role,
    Story,
)
from ai_story_writer.utils.cli import dump_story
from ai_story_writer.utils.yaml import YamlStoryDocument


def _args(story_file: Path, **overrides) -> Namespace:
    values = {
        'file': str(story_file),
        'id': None,
        'model': 'test.model',
        'template': 'prompt',
        'convo': False,
        'dry_run': False,
    }
    values.update(overrides)
    return Namespace(**values)


def _write_story(tmp_path: Path, story: Story) -> Path:
    story_file = tmp_path / 'story.yaml'
    story_file.write_text(YamlStoryDocument.from_story(story).dump())
    _, md = dump_story(story)
    if md:
        story_file.with_suffix('.md').write_text(md)
    return story_file


def test_generate_dry_run(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(
        tmp_path,
        Story(
            title='Story',
            chapters=[
                Chapter(id=str(uuid4()), outline='Existing', content='Body'),
                Chapter(outline='Next'),
            ],
        ),
    )
    original_yaml = story_file.read_text()
    original_md = story_file.with_suffix('.md').read_text()
    create_messages = mocker.patch.object(
        cli,
        'create_messages',
        return_value=[Message(role=Role.USER, content='Rendered prompt')],
    )
    count_input_tokens = mocker.patch.object(cli, 'count_input_tokens', return_value=123)

    cli.generate(_args(story_file, dry_run=True))

    assert capsys.readouterr().out == 'Rendered prompt\nInput tokens: 123\n'
    assert story_file.read_text() == original_yaml
    assert story_file.with_suffix('.md').read_text() == original_md
    generated_story, chapter_index, template, include_full_convo = create_messages.call_args.args
    assert generated_story.title == 'Story'
    assert generated_story.id is not None
    assert chapter_index == 1
    assert template == 'prompt'
    assert include_full_convo is False
    count_input_tokens.assert_called_once_with(
        [Message(role=Role.USER, content='Rendered prompt')],
        LlmModel(provider='test', name='model'),
    )


def test_generate_dry_run_inlcude_full_convo(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(tmp_path, Story(title='Story', chapters=[Chapter(outline='Outline')]))
    mocker.patch.object(
        cli,
        'create_messages',
        return_value=[
            Message(role=Role.SYSTEM, content='System'),
            Message(role=Role.USER, content='Outline'),
        ],
    )

    cli.generate(_args(story_file, dry_run=True, convo=True, model=None))

    assert capsys.readouterr().out == '[system]\nSystem\n\n[user]\nOutline\n'


def test_generate_dry_run_no_token_count(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(tmp_path, Story(title='Story', chapters=[Chapter(outline='Outline')]))
    mocker.patch.object(
        cli,
        'create_messages',
        return_value=[Message(role=Role.USER, content='Rendered prompt')],
    )
    count_input_tokens = mocker.patch.object(cli, 'count_input_tokens', return_value=None)

    cli.generate(_args(story_file, dry_run=True, model='Ollama.model'))

    assert capsys.readouterr().out == 'Rendered prompt\n'
    count_input_tokens.assert_called_once()


def test_generate_write(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(
        tmp_path,
        Story(title='Story', chapters=[Chapter(lore='Lore', outline='Outline')]),
    )
    story_id = UUID('00000000-0000-0000-0000-000000000001')
    chapter_id = '00000000-0000-0000-0000-000000000002'
    mocker.patch.object(cli, 'uuid4', return_value=story_id)
    mocker.patch.object(cli, 'generate_id', return_value=chapter_id)
    generate_chapter = mocker.patch.object(
        cli,
        'generate_chapter',
        return_value=[
            GenerationInProgressEvent(chunk='# Chapter'),
            GenerationInProgressEvent(chunk='\n\nBody'),
            GenerationCompletedEvent(content='# Chapter\n\nBody'),
        ],
    )

    cli.generate(_args(story_file))

    assert capsys.readouterr().out == '# Chapter\n\nBody'
    generated_story = YamlStoryDocument.load(story_file.read_text(), story_file.with_suffix('.md').read_text()).story
    assert generated_story.id == str(story_id)
    assert generated_story.chapters == [
        Chapter(id=chapter_id, lore='Lore', outline='Outline', content='# Chapter\n\nBody')
    ]
    call_story, chapter_index, model, template, include_full_convo = generate_chapter.call_args.args
    assert call_story == generated_story
    assert chapter_index == 0
    assert model == LlmModel(provider='test', name='model')
    assert template == 'prompt'
    assert include_full_convo is False


def test_generate_error(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(tmp_path, Story(title='Story', chapters=[Chapter(outline='Outline')]))
    original_yaml = story_file.read_text()
    mocker.patch.object(
        cli,
        'generate_chapter',
        return_value=[GenerationErrorEvent(message='provider failed')],
    )

    cli.generate(_args(story_file))

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == 'Encountered error provider failed\n'
    assert story_file.read_text() == original_yaml
    assert not story_file.with_suffix('.md').exists()


@pytest.mark.parametrize(
    ('chapter_id', 'story', 'message'),
    [
        (
            None,
            Story(
                title='Story',
                chapters=[Chapter(id='00000000-0000-0000-0000-000000000001', outline='Outline')],
            ),
            'Cannot find chapter without id',
        ),
        (
            '00000000-0000-0000-0000-000000000002',
            Story(
                title='Story',
                chapters=[Chapter(id='00000000-0000-0000-0000-000000000001', outline='Outline')],
            ),
            'Cannot find chapter with id 00000000-0000-0000-0000-000000000002',
        ),
    ],
)
def test_generate_missing_chapter(tmp_path: Path, chapter_id: str | None, story: Story, message: str):
    story_file = _write_story(tmp_path, story)

    with pytest.raises(KeyError, match=message):
        cli.generate(_args(story_file, id=chapter_id, dry_run=True))


def test_start_dry_run_without_model(mocker: MockerFixture):
    run = mocker.Mock()
    args = Namespace(command='generate', file='story.yaml', dry_run=True, model=None, func=run)
    mocker.patch.object(cli.parser, 'parse_args', return_value=args)
    setup = mocker.patch.object(cli, 'setup')
    teardown = mocker.patch.object(cli, 'teardown')

    cli.start()

    run.assert_called_once_with(args)
    setup.assert_not_called()
    teardown.assert_not_called()


def test_start_dry_run_with_model(mocker: MockerFixture):
    run = mocker.Mock()
    args = Namespace(command='generate', file='story.yaml', dry_run=True, model='OpenAI.model', func=run)
    mocker.patch.object(cli.parser, 'parse_args', return_value=args)
    setup = mocker.patch.object(cli, 'setup')
    teardown = mocker.patch.object(cli, 'teardown')

    cli.start()

    setup.assert_called_once_with()
    run.assert_called_once_with(args)
    teardown.assert_called_once_with()


def test_start_generation_error(mocker: MockerFixture):
    run = mocker.Mock(side_effect=RuntimeError('generation failed'))
    args = Namespace(command='generate', file='story.yaml', dry_run=False, model='test.model', func=run)
    mocker.patch.object(cli.parser, 'parse_args', return_value=args)
    setup = mocker.patch.object(cli, 'setup')
    teardown = mocker.patch.object(cli, 'teardown')

    with pytest.raises(RuntimeError, match='generation failed'):
        cli.start()

    setup.assert_called_once_with()
    run.assert_called_once_with(args)
    teardown.assert_called_once_with()


def test_start_requires_model_for_generation(mocker: MockerFixture):
    mocker.patch.object(
        cli.parser,
        'parse_args',
        return_value=Namespace(command='generate', dry_run=False, model=None),
    )
    parser_error = mocker.patch.object(cli.parser, 'error', side_effect=SystemExit(2))
    setup = mocker.patch.object(cli, 'setup')

    with pytest.raises(SystemExit):
        cli.start()

    parser_error.assert_called_once_with('the following arguments are required: -m/--model')
    setup.assert_not_called()


def test_start_rejects_txt(mocker: MockerFixture):
    args = Namespace(command='generate', file='story.txt', dry_run=False, model='test.model', func=mocker.Mock())
    mocker.patch.object(cli.parser, 'parse_args', return_value=args)
    parser_error = mocker.patch.object(cli.parser, 'error', side_effect=SystemExit(2))
    setup = mocker.patch.object(cli, 'setup')

    with pytest.raises(SystemExit):
        cli.start()

    parser_error.assert_called_once_with(
        'Story instruction file must use the .yaml extension: story.txt. '
        'Migrate legacy TXT files with: cli migrate --file story.txt'
    )
    setup.assert_not_called()


def test_start_migration_does_not_initialize_clients(mocker: MockerFixture):
    run = mocker.Mock()
    args = Namespace(command='migrate', file='story.txt', func=run)
    mocker.patch.object(cli.parser, 'parse_args', return_value=args)
    setup = mocker.patch.object(cli, 'setup')
    teardown = mocker.patch.object(cli, 'teardown')

    cli.start()

    run.assert_called_once_with(args)
    setup.assert_not_called()
    teardown.assert_not_called()


def test_migrate(tmp_path: Path, capsys: CaptureFixture[str]):
    story = Story(
        title='Story',
        style='Lyrical\nRestrained',
        chapter_count=2,
        chapters=[
            Chapter(lore='Shared lore\nSecond line', outline='First\nBeat', content='# First\n\nBody'),
            Chapter(outline='Second', content='# Second\n\nEnding'),
        ],
    )
    txt, md = dump_story(story)
    txt_file = tmp_path / 'story.txt'
    md_file = tmp_path / 'story.md'
    txt_file.write_text(txt)
    md_file.write_text(md)

    cli.migrate(Namespace(file=str(txt_file)))

    yaml_file = tmp_path / 'story.yaml'
    assert capsys.readouterr().out == f'Migrated {txt_file} to {yaml_file}\n'
    assert txt_file.read_text() == txt
    assert md_file.read_text() == md
    assert YamlStoryDocument.load(yaml_file.read_text(), md_file.read_text()).story == story
    assert 'id:' not in yaml_file.read_text()


def test_migrate_refuses_existing_yaml(tmp_path: Path):
    txt_file = tmp_path / 'story.txt'
    yaml_file = tmp_path / 'story.yaml'
    txt_file.write_text('Story\n\n---\n\nOutline')
    yaml_file.write_text('existing')

    with pytest.raises(cli.CliError, match='Refusing to overwrite'):
        cli.migrate(Namespace(file=str(txt_file)))

    assert yaml_file.read_text() == 'existing'


def test_migrate_requires_txt(tmp_path: Path):
    source = tmp_path / 'story.md'
    source.write_text('Story')

    with pytest.raises(cli.CliError, match=r'must use the \.txt extension'):
        cli.migrate(Namespace(file=str(source)))

    assert not source.with_suffix('.yaml').exists()


def test_migrate_invalid_txt(tmp_path: Path):
    source = tmp_path / 'story.txt'
    source.write_text('Story\n\nStyle\n\nnot-a-chapter-count')

    with pytest.raises(cli.CliError, match='Could not migrate'):
        cli.migrate(Namespace(file=str(source)))

    assert not source.with_suffix('.yaml').exists()


def test_generate_requires_yaml(tmp_path: Path):
    source = tmp_path / 'story.txt'
    source.write_text('Story\n\n---\n\nOutline')

    with pytest.raises(cli.CliError, match=r'must use the \.yaml extension'):
        cli.generate(_args(source, dry_run=True))
