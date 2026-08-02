import pytest

from ai_story_writer.lib.story import find_chapter_index
from ai_story_writer.types import Chapter, Story


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
