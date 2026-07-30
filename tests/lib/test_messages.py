import pytest
from jinja2 import Environment

from ai_story_writer.lib.messages import create_messages
from ai_story_writer.types import Chapter, Message, Role, Story


def test_create_messages(template_environment: Environment):
    story = Story(
        title='Story',
        style='Noir',
        chapters=[
            Chapter(outline='First outline', content='# First\n\nFirst body', lore='Original lore'),
            Chapter(outline='Second outline', content='# Second\n\nSecond body', lore='Updated lore'),
            Chapter(outline='Third outline'),
            Chapter(outline='Fourth outline'),
        ],
    )

    messages = create_messages(story, 2, 'prompt', full_chapter_count=1)

    assert messages == [
        Message(
            role=Role.USER,
            content=(
                'title=Story|style=Noir|lore=Updated lore|summary=# First\n\nFirst outline|'
                'previous=# Second\n\nSecond body|current=Third outline|next=Fourth outline'
            ),
        )
    ]


def test_create_messages_first_chapter(template_environment: Environment):
    story = Story(title='Story', chapters=[Chapter(outline='First'), Chapter(outline='Second')])

    messages = create_messages(story, 0, 'prompt')

    assert messages[0].content == ('title=Story|style=None|lore=None|summary=None|previous=|current=First|next=Second')


def test_create_messages_include_full_conversation(template_environment: Environment):
    story = Story(
        title='Story',
        style='Noir',
        chapters=[
            Chapter(outline='First outline', content='# First\n\nFirst body', lore='Lore'),
            Chapter(outline='Second outline', content='Second body'),
            Chapter(outline='Third outline'),
        ],
    )

    messages = create_messages(story, 2, 'convo', include_full_conversation=True)

    assert messages == [
        Message(role=Role.SYSTEM, content='title=Story|style=Noir|lore=Lore'),
        Message(role=Role.USER, content='First outline'),
        Message(role=Role.ASSISTANT, content='# First\n\nFirst body'),
        Message(role=Role.USER, content='Second outline'),
        Message(role=Role.ASSISTANT, content='Second body'),
        Message(role=Role.USER, content='Third outline'),
    ]


@pytest.mark.parametrize('chapter_index', [-1, 1])
def test_create_messages_invalid_index(template_environment: Environment, chapter_index: int):
    story = Story(title='Story', chapters=[Chapter(outline='Outline')])

    with pytest.raises(IndexError, match=f'chapter index {chapter_index} out of range'):
        create_messages(story, chapter_index, 'prompt')


def test_create_messages_requires_previous_content(template_environment: Environment):
    story = Story(
        title='Story',
        chapters=[Chapter(outline='Missing content'), Chapter(outline='Current outline')],
    )

    with pytest.raises(ValueError, match='chapter content is missing'):
        create_messages(story, 1, 'prompt')
