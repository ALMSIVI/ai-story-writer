import pytest

from uuid import UUID
from pytest_mock import MockerFixture

from ai_story_writer.lib import story as story_module
from ai_story_writer.lib.story import (
    find_chapter_index,
    generate_id,
    get_lore,
    get_next_outline,
    get_previous_context,
)
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


@pytest.mark.parametrize(
    ('chapter_index', 'expected'),
    [
        (0, 'Original lore'),
        (1, 'Original lore'),
        (2, 'Updated lore'),
    ],
)
def test_get_lore_uses_nearest_lore(chapter_index: int, expected: str):
    story = Story(
        title='Story',
        chapters=[
            Chapter(outline='First', lore='Original lore'),
            Chapter(outline='Second'),
            Chapter(outline='Third', lore='Updated lore'),
        ],
    )

    assert get_lore(story, chapter_index) == expected


def test_get_lore_returns_none_when_unavailable():
    story = Story(title='Story', chapters=[Chapter(outline='First')])

    assert get_lore(story, 0) is None


@pytest.mark.parametrize(
    ('full_chapter_count', 'expected'),
    [
        (None, (None, '# First\n\nFirst body\n\nSecond body')),
        (1, ('# First\n\nFirst outline', 'Second body')),
        (0, ('# First\n\nFirst outline\n\nSecond outline', '')),
    ],
)
def test_get_previous_context(full_chapter_count: int | None, expected: tuple[str | None, str]):
    story = Story(
        title='Story',
        chapters=[
            Chapter(outline='First outline', content='# First\n\nFirst body'),
            Chapter(outline='Second outline', content='Second body'),
            Chapter(outline='Third outline'),
        ],
    )

    assert get_previous_context(story, 2, full_chapter_count) == expected


def test_get_previous_context_for_first_chapter():
    story = Story(title='Story', chapters=[Chapter(outline='First')])

    assert get_previous_context(story, 0, None) == (None, '')


@pytest.mark.parametrize(
    ('chapter_index', 'expected'),
    [
        (0, 'Second'),
        (1, None),
    ],
)
def test_get_next_outline(chapter_index: int, expected: str | None):
    story = Story(title='Story', chapters=[Chapter(outline='First'), Chapter(outline='Second')])

    assert get_next_outline(story, chapter_index) == expected
