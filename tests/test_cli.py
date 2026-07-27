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
    GenerationConfig,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
    Message,
    Role,
    Story,
)
from ai_story_writer.utils.markdown import dump_markdown
from ai_story_writer.utils.yaml import YamlStoryDocument


def _args(story_file: Path, **overrides) -> Namespace:
    values = {
        'file': str(story_file),
        'id': None,
        'config': None,
        'dry_run': False,
    }
    values.update(overrides)
    return Namespace(**values)


def _write_story(
    tmp_path: Path,
    story: Story,
    generation_config: GenerationConfig | None = None,
) -> Path:
    story_file = tmp_path / 'story.yaml'
    (tmp_path / 'config.json').write_text(
        '{"model":"test.model","template":"prompt","includeFullConversation":false,"fullChapterCount":1}'
    )
    story_file.write_text(YamlStoryDocument.from_story(story, generation_config).dump())
    md = dump_markdown(story)
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
    setup = mocker.patch.object(cli, 'setup')
    teardown = mocker.patch.object(cli, 'teardown')

    cli.generate(_args(story_file, dry_run=True))

    assert capsys.readouterr().out == 'Rendered prompt\nInput tokens: 123\n'
    assert story_file.read_text() == original_yaml
    assert story_file.with_suffix('.md').read_text() == original_md
    generated_story, chapter_index, template = create_messages.call_args.args
    assert generated_story.title == 'Story'
    assert generated_story.id is not None
    assert chapter_index == 1
    assert template == 'prompt'
    assert create_messages.call_args.kwargs == {
        'include_full_conversation': False,
        'full_chapter_count': 1,
    }
    count_input_tokens.assert_called_once_with(
        [Message(role=Role.USER, content='Rendered prompt')],
        LlmModel(provider='test', name='model'),
    )
    setup.assert_called_once_with()
    teardown.assert_called_once_with()


def test_generate_dry_run_include_full_conversation(
    tmp_path: Path,
    mocker: MockerFixture,
    capsys: CaptureFixture[str],
):
    story_file = _write_story(
        tmp_path,
        Story(
            title='Story',
            chapters=[Chapter(outline='Outline')],
        ),
        GenerationConfig(includeFullConversation=True),
    )
    create_messages = mocker.patch.object(
        cli,
        'create_messages',
        return_value=[
            Message(role=Role.SYSTEM, content='System'),
            Message(role=Role.USER, content='Outline'),
        ],
    )
    mocker.patch.object(cli, 'count_input_tokens', return_value=None)
    mocker.patch.object(cli, 'setup')
    mocker.patch.object(cli, 'teardown')

    cli.generate(_args(story_file, dry_run=True))

    assert capsys.readouterr().out == '[system]\nSystem\n\n[user]\nOutline\n'
    assert create_messages.call_args.kwargs['include_full_conversation'] is True


def test_generate_dry_run_without_model_skips_setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    capsys: CaptureFixture[str],
):
    monkeypatch.chdir(tmp_path)
    story_file = tmp_path / 'story.yaml'
    story_file.write_text('title: Story\nconfig:\n  template: prompt\nchapters:\n  - outline: Outline\n')
    mocker.patch.object(
        cli,
        'create_messages',
        return_value=[Message(role=Role.USER, content='Rendered prompt')],
    )
    setup = mocker.patch.object(cli, 'setup')
    teardown = mocker.patch.object(cli, 'teardown')

    cli.generate(_args(story_file, dry_run=True))

    assert capsys.readouterr().out == 'Rendered prompt\n'
    setup.assert_not_called()
    teardown.assert_not_called()


def test_generate_dry_run_no_token_count(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(
        tmp_path,
        Story(
            title='Story',
            chapters=[Chapter(outline='Outline')],
        ),
        GenerationConfig(model='Ollama.model'),
    )
    mocker.patch.object(
        cli,
        'create_messages',
        return_value=[Message(role=Role.USER, content='Rendered prompt')],
    )
    count_input_tokens = mocker.patch.object(cli, 'count_input_tokens', return_value=None)
    mocker.patch.object(cli, 'setup')
    mocker.patch.object(cli, 'teardown')

    cli.generate(_args(story_file, dry_run=True))

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
    setup = mocker.patch.object(cli, 'setup')
    teardown = mocker.patch.object(cli, 'teardown')

    cli.generate(_args(story_file))

    assert capsys.readouterr().out == '# Chapter\n\nBody'
    generated_story = YamlStoryDocument.load(story_file.read_text(), story_file.with_suffix('.md').read_text()).story
    assert generated_story.id == str(story_id)
    assert generated_story.chapters == [
        Chapter(id=chapter_id, lore='Lore', outline='Outline', content='# Chapter\n\nBody')
    ]
    call_story, chapter_index, model, template = generate_chapter.call_args.args
    assert call_story == generated_story
    assert chapter_index == 0
    assert model == LlmModel(provider='test', name='model')
    assert template == 'prompt'
    assert generate_chapter.call_args.kwargs == {
        'include_full_conversation': False,
        'full_chapter_count': 1,
    }
    setup.assert_called_once_with()
    teardown.assert_called_once_with()


def test_generate_error(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(tmp_path, Story(title='Story', chapters=[Chapter(outline='Outline')]))
    original_yaml = story_file.read_text()
    mocker.patch.object(
        cli,
        'generate_chapter',
        return_value=[GenerationErrorEvent(message='provider failed')],
    )
    mocker.patch.object(cli, 'setup')
    teardown = mocker.patch.object(cli, 'teardown')

    cli.generate(_args(story_file))

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == 'Encountered error provider failed\n'
    assert story_file.read_text() == original_yaml
    assert not story_file.with_suffix('.md').exists()
    teardown.assert_called_once_with()


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


def test_generate_requires_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture):
    monkeypatch.chdir(tmp_path)
    story_file = tmp_path / 'story.yaml'
    story_file.write_text('title: Story\nconfig:\n  template: prompt\nchapters:\n  - outline: Outline\n')
    setup = mocker.patch.object(cli, 'setup')

    with pytest.raises(cli.CliError, match='No model configured'):
        cli.generate(_args(story_file))

    setup.assert_not_called()
