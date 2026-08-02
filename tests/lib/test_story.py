import pytest

from uuid import UUID
from pytest_mock import MockerFixture

from ai_story_writer.lib import story as story_module
from ai_story_writer.lib.story import generate_id, find_chapter_index
from ai_story_writer.types import Chapter, Story


def test_generate_id_retries_collision(mocker: MockerFixture):
    existing = '00000000-0000-0000-0000-000000000001'
    new = '00000000-0000-0000-0000-000000000002'
    uuid4 = mocker.patch.object(story_module, 'uuid4', side_effect=[UUID(existing), UUID(new)])

    result = generate_id([Chapter(id=existing, outline='Outline')])

    assert result == new
    assert uuid4.call_count == 2


def test_find_chapter_without_id():
    story = Story(
        title='Story',
        chapters=[Chapter(id='first', outline='First'), Chapter(outline='Second')],
    )

    assert find_chapter_index(story, None) == 1


def test_find_chapter_by_id():
    story = Story(
        title='Story',
        chapters=[Chapter(id='first', outline='First'), Chapter(id='second', outline='Second')],
    )

    assert find_chapter_index(story, 'second') == 1


@pytest.mark.parametrize(
    ('chapter_id', 'message'),
    [
        (None, 'Cannot find chapter without id'),
        ('missing', 'Cannot find chapter with id missing'),
    ],
)
def test_find_chapter_errors(chapter_id: str | None, message: str):
    story = Story(title='Story', chapters=[Chapter(id='first', outline='First')])

    with pytest.raises(KeyError, match=message):
        find_chapter_index(story, chapter_id)
