import pytest
from jinja2 import Environment

from ai_story_writer.lib import llm
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
from tests.conftest import MockClient


def test_create_messages(template_environment: Environment):
    story = Story(
        title='Story',
        style='Noir',
        chapter_count=1,
        chapters=[
            Chapter(outline='First outline', content='# First\n\nFirst body', lore='Original lore'),
            Chapter(outline='Second outline', content='# Second\n\nSecond body', lore='Updated lore'),
            Chapter(outline='Third outline'),
            Chapter(outline='Fourth outline'),
        ],
    )

    messages = llm.create_messages(story, 2, 'prompt')

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

    messages = llm.create_messages(story, 0, 'prompt')

    assert messages[0].content == ('title=Story|style=None|lore=None|summary=None|previous=|current=First|next=Second')


def test_create_messages_include_full_convo(template_environment: Environment):
    story = Story(
        title='Story',
        style='Noir',
        chapters=[
            Chapter(outline='First outline', content='# First\n\nFirst body', lore='Lore'),
            Chapter(outline='Second outline', content='Second body'),
            Chapter(outline='Third outline'),
        ],
    )

    messages = llm.create_messages(story, 2, 'convo', include_full_convo=True)

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
        llm.create_messages(story, chapter_index, 'prompt')


def test_create_messages_requires_previous_content(template_environment: Environment):
    story = Story(
        title='Story',
        chapters=[Chapter(outline='Missing content'), Chapter(outline='Current outline')],
    )

    with pytest.raises(ValueError, match='chapter content is missing'):
        llm.create_messages(story, 1, 'prompt')


def test_generate_chapter(template_environment: Environment):
    client = MockClient(chunks=['First ', 'second'])
    llm.clients['test'] = client
    story = Story(title='Story', chapters=[Chapter(outline='Outline')])
    model = LlmModel(provider='test', name='model')

    events = list(llm.generate_chapter(story, 0, model, 'prompt'))

    assert events == [
        GenerationInProgressEvent(chunk='First '),
        GenerationInProgressEvent(chunk='second'),
        GenerationCompletedEvent(content='First second'),
    ]
    assert len(client.calls) == 1
    messages, model_name = client.calls[0]
    assert model_name == 'model'
    assert len(messages) == 1
    assert messages[0].role == Role.USER
    assert 'current=Outline' in messages[0].content


def test_generate_chapter_error(template_environment: Environment):
    client = MockClient(error=RuntimeError('provider failed'))
    llm.clients['test'] = client
    story = Story(title='Story', chapters=[Chapter(outline='Outline')])

    events = list(llm.generate_chapter(story, 0, LlmModel(provider='test', name='model'), 'prompt'))

    assert events == [GenerationErrorEvent(message='provider failed')]


def test_generate_chapter_missing_client(template_environment: Environment):
    story = Story(title='Story', chapters=[Chapter(outline='Outline')])

    with pytest.raises(ValueError, match='client missing does not exist'):
        list(llm.generate_chapter(story, 0, LlmModel(provider='missing', name='model'), 'prompt'))


def test_generate_chapter_unsupported_model(template_environment: Environment):
    llm.clients['test'] = MockClient()
    story = Story(title='Story', chapters=[Chapter(outline='Outline')])

    with pytest.raises(ValueError, match='model unsupported not supported in client test'):
        list(llm.generate_chapter(story, 0, LlmModel(provider='test', name='unsupported'), 'prompt'))


def test_cleanup_clients():
    first = MockClient()
    second = MockClient()
    llm.clients.update({'first': first, 'second': second})

    llm.cleanup_clients()

    assert first.closed
    assert second.closed
    assert llm.clients == {}
