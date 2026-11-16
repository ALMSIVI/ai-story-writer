import pytest

from uuid import UUID
from pytest_mock import MockerFixture

from ai_story_writer.lib import story as story_module
from ai_story_writer.lib.story import (
    find_chapter_index,
    generate_id,
    get_background,
    get_next_outline,
    get_previous_context,
)
from ai_story_writer.types import Background, Chapter, Story


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
        (0, ['Original background']),
        (1, ['Original background']),
        (2, ['Updated background']),
    ],
)
def test_get_background_uses_nearest_background(chapter_index: int, expected: list[str]):
    story = Story(
        title='Story',
        chapters=[
            Chapter(outline='First', background=['Original background']),
            Chapter(outline='Second'),
            Chapter(outline='Third', background=['Updated background']),
        ],
    )

    assert get_background(story, chapter_index) == expected


def test_get_background_returns_none_when_unavailable():
    story = Story(title='Story', chapters=[Chapter(outline='First')])

    assert get_background(story, 0) is None


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


@pytest.mark.parametrize(
    'chapter_index, expected',
    [
        (0, ['World', 'Principles']),
        (1, ['World', 'Principles', 'Original chapter setting']),
        (2, ['World', 'Principles', 'Original chapter setting']),
        (3, ['World', 'Principles', 'Updated chapter setting']),
        (4, ['World', 'Principles']),
        (5, ['World', 'Principles']),
    ],
)
def test_background_combines_story_and_inherited_chapter_items(chapter_index: int, expected: list[str]):
    story = Story(
        title='Story',
        background=['World', 'Principles'],
        chapters=[
            Chapter(outline='First'),
            Chapter(outline='Second', background=['Original chapter setting']),
            Chapter(outline='Third'),
            Chapter(outline='Fourth', background=['Updated chapter setting']),
            Chapter(outline='Fifth', background=[]),
            Chapter(outline='Sixth'),
        ],
    )

    assert get_background(story, chapter_index) == expected


def test_background_resolution_does_not_modify_source_lists():
    story = Story(
        title='Story',
        background=['World'],
        chapters=[Chapter(outline='First', background=['Chapter setting'])],
    )

    assert get_background(story, 0) == ['World', 'Chapter setting']
    assert get_background(story, 0) == ['World', 'Chapter setting']
    assert story.background == [Background(content='World')]
    assert story.chapters[0].background == [Background(content='Chapter setting')]


@pytest.mark.parametrize(
    'outline, expected',
    [
        (
            'MARA visits the western gate',
            ['General', 'Unconditional object', 'Mara details', 'Gate rules', 'Chapter facts', 'Local details'],
        ),
        ('The gatehouse opens', ['General', 'Unconditional object', 'Gate rules', 'Chapter facts']),
        ('An unrelated scene', ['General', 'Unconditional object', 'Chapter facts']),
    ],
)
def test_background_filters_story_and_inherited_items_against_current_outline(outline: str, expected: list[str]):
    story = Story.model_validate(
        {
            'title': 'Story',
            'background': [
                'General',
                {'content': 'Unconditional object'},
                {'keywords': ['Mara', 'western gate'], 'content': 'Mara details'},
                {'keywords': ['gate'], 'content': 'Gate rules'},
                {'keywords': [], 'content': 'Never included'},
            ],
            'chapters': [
                {
                    'outline': 'An unrelated scene',
                    'background': ['Chapter facts', {'keywords': ['mara'], 'content': 'Local details'}],
                },
                {'outline': outline},
            ],
        }
    )

    assert get_background(story, 1) == expected
    assert get_background(story, 0) == ['General', 'Unconditional object', 'Chapter facts']


def test_empty_chapter_background_keeps_matching_story_items():
    story = Story.model_validate(
        {
            'title': 'Story',
            'background': [{'keywords': ['gate'], 'content': 'Gate rules'}],
            'chapters': [
                {'outline': 'Gate', 'background': ['Old chapter facts']},
                {'outline': 'Gate', 'background': []},
                {'outline': 'Gate'},
            ],
        }
    )

    assert get_background(story, 2) == ['Gate rules']
