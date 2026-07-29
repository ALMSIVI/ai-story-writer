from argparse import Namespace
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from ai_story_writer.commands import CommandError
from ai_story_writer.commands import write as write_command
from ai_story_writer.lib.markdown import dump_markdown
from ai_story_writer.lib.yaml import YamlStoryDocument
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


def test_write_dry_run(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
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
        write_command,
        'create_messages',
        return_value=[Message(role=Role.USER, content='Rendered prompt')],
    )
    count_input_tokens = mocker.patch.object(write_command, 'count_input_tokens', return_value=123)
    setup = mocker.patch.object(write_command, 'setup')
    teardown = mocker.patch.object(write_command, 'teardown')

    write_command.write(_args(story_file, dry_run=True))

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


def test_write_dry_run_include_full_conversation(
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
        write_command,
        'create_messages',
        return_value=[
            Message(role=Role.SYSTEM, content='System'),
            Message(role=Role.USER, content='Outline'),
        ],
    )
    mocker.patch.object(write_command, 'count_input_tokens', return_value=None)
    mocker.patch.object(write_command, 'setup')
    mocker.patch.object(write_command, 'teardown')

    write_command.write(_args(story_file, dry_run=True))

    assert capsys.readouterr().out == '[system]\nSystem\n\n[user]\nOutline\n'
    assert create_messages.call_args.kwargs['include_full_conversation'] is True


def test_write_dry_run_without_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    capsys: CaptureFixture[str],
):
    monkeypatch.chdir(tmp_path)
    story_file = tmp_path / 'story.yaml'
    story_file.write_text('title: Story\nconfig:\n  template: prompt\nchapters:\n  - outline: Outline\n')
    mocker.patch.object(
        write_command,
        'create_messages',
        return_value=[Message(role=Role.USER, content='Rendered prompt')],
    )
    setup = mocker.patch.object(write_command, 'setup')
    teardown = mocker.patch.object(write_command, 'teardown')

    write_command.write(_args(story_file, dry_run=True))

    assert capsys.readouterr().out == 'Rendered prompt\n'
    setup.assert_not_called()
    teardown.assert_not_called()


def test_write_dry_run_no_token_count(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(
        tmp_path,
        Story(
            title='Story',
            chapters=[Chapter(outline='Outline')],
        ),
        GenerationConfig(model='Ollama.model'),
    )
    mocker.patch.object(
        write_command,
        'create_messages',
        return_value=[Message(role=Role.USER, content='Rendered prompt')],
    )
    count_input_tokens = mocker.patch.object(write_command, 'count_input_tokens', return_value=None)
    mocker.patch.object(write_command, 'setup')
    mocker.patch.object(write_command, 'teardown')

    write_command.write(_args(story_file, dry_run=True))

    assert capsys.readouterr().out == 'Rendered prompt\n'
    count_input_tokens.assert_called_once()


def test_write_persists_chapter(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(
        tmp_path,
        Story(title='Story', chapters=[Chapter(lore='Lore', outline='Outline')]),
    )
    story_id = UUID('00000000-0000-0000-0000-000000000001')
    chapter_id = '00000000-0000-0000-0000-000000000002'
    mocker.patch.object(write_command, 'uuid4', return_value=story_id)
    mocker.patch.object(write_command, 'generate_id', return_value=chapter_id)
    write_chapter = mocker.patch.object(
        write_command,
        'write_chapter',
        return_value=[
            GenerationInProgressEvent(chunk='# Chapter'),
            GenerationInProgressEvent(chunk='\n\nBody'),
            GenerationCompletedEvent(content='# Chapter\n\nBody'),
        ],
    )
    setup = mocker.patch.object(write_command, 'setup')
    teardown = mocker.patch.object(write_command, 'teardown')

    write_command.write(_args(story_file))

    assert capsys.readouterr().out == '# Chapter\n\nBody'
    generated_story = YamlStoryDocument.load(story_file.read_text(), story_file.with_suffix('.md').read_text()).story
    assert generated_story.id == str(story_id)
    assert generated_story.chapters == [
        Chapter(id=chapter_id, lore='Lore', outline='Outline', content='# Chapter\n\nBody')
    ]
    call_story, chapter_index, model, template = write_chapter.call_args.args
    assert call_story == generated_story
    assert chapter_index == 0
    assert model == LlmModel(provider='test', name='model')
    assert template == 'prompt'
    assert write_chapter.call_args.kwargs == {
        'include_full_conversation': False,
        'full_chapter_count': 1,
    }
    setup.assert_called_once_with()
    teardown.assert_called_once_with()


def test_write_error(tmp_path: Path, mocker: MockerFixture, capsys: CaptureFixture[str]):
    story_file = _write_story(tmp_path, Story(title='Story', chapters=[Chapter(outline='Outline')]))
    original_yaml = story_file.read_text()
    mocker.patch.object(
        write_command,
        'write_chapter',
        return_value=[GenerationErrorEvent(message='provider failed')],
    )
    mocker.patch.object(write_command, 'setup')
    teardown = mocker.patch.object(write_command, 'teardown')

    write_command.write(_args(story_file))

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
def test_write_missing_chapter(tmp_path: Path, chapter_id: str | None, story: Story, message: str):
    story_file = _write_story(tmp_path, story)

    with pytest.raises(KeyError, match=message):
        write_command.write(_args(story_file, id=chapter_id, dry_run=True))


def test_write_requires_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture):
    monkeypatch.chdir(tmp_path)
    story_file = tmp_path / 'story.yaml'
    story_file.write_text('title: Story\nconfig:\n  template: prompt\nchapters:\n  - outline: Outline\n')
    setup = mocker.patch.object(write_command, 'setup')

    with pytest.raises(CommandError, match='No model configured'):
        write_command.write(_args(story_file))

    setup.assert_not_called()
