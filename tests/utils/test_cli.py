from uuid import uuid4

import pytest

from ai_story_writer.types import Chapter, Story
from ai_story_writer.utils.cli import dump_story, parse_files


@pytest.mark.parametrize(
    'story',
    [
        Story(title='Title', chapters=[Chapter(outline='Outline')]),
        Story(title='Title', style='Noir', chapters=[Chapter(outline='Outline')]),
        Story(title='Title', chapter_count=2, chapters=[Chapter(outline='Outline')]),
        Story(title='Title', style='Noir', chapter_count=2, chapters=[Chapter(outline='Outline')]),
        Story(id=str(uuid4()), title='Title', chapters=[Chapter(outline='Outline')]),
        Story(id=str(uuid4()), title='Title', style='Noir', chapters=[Chapter(outline='Outline')]),
        Story(id=str(uuid4()), title='Title', chapter_count=2, chapters=[Chapter(outline='Outline')]),
    ],
)
def test_story_round_trip(story: Story):
    txt, md = dump_story(story)

    assert parse_files(txt, md) == story


@pytest.mark.parametrize(
    'chapter',
    [
        Chapter(outline='Outline'),
        Chapter(id=str(uuid4()), outline='Outline'),
        Chapter(lore='Lore', outline='Outline'),
        Chapter(id=str(uuid4()), lore='Lore', outline='Outline'),
        Chapter(outline='Outline', content='Untitled body'),
        Chapter(outline='Outline', content='# Chapter Name\n\nTitled body'),
    ],
)
def test_chapter_round_trip(chapter: Chapter):
    story = Story(title='Title', chapters=[chapter])
    txt, md = dump_story(story)

    assert parse_files(txt, md) == story


def test_story_with_multiple_chapters_round_trip():
    story = Story(
        title='Title',
        chapters=[
            Chapter(id=str(uuid4()), lore='Shared lore', outline='First outline', content='# First\n\nFirst body'),
            Chapter(id=str(uuid4()), outline='Second outline', content='# Second\n\nSecond body'),
            Chapter(outline='Third outline'),
        ],
    )

    txt, md = dump_story(story)

    assert parse_files(txt, md) == story
    assert md == '# First\n\nFirst body\n\n# Second\n\nSecond body'


def test_markdown_with_multiple_chapters():
    txt = 'Story\n\n---\n\nFirst outline\n\n---\n\nSecond outline'
    md = '# First\n\nBody\n\n## Subheading\n\nMore\n\n# Second\n\nEnding'

    story = parse_files(txt, md)

    assert story.chapters[0].title == 'First'
    assert story.chapters[0].content == 'Body\n\n## Subheading\n\nMore'
    assert story.chapters[1].title == 'Second'
    assert story.chapters[1].content == 'Ending'
