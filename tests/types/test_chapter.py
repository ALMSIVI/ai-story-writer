import pytest

from ai_story_writer.types import Chapter


def test_extracts_title():
    chapter = Chapter(outline='Outline', content='# A Title\n\nBody text')

    assert chapter.title == 'A Title'
    assert chapter.content == 'Body text'
    assert chapter.full_content == '# A Title\n\nBody text'
    assert chapter.full_outline == '# A Title\n\nOutline'


def test_does_not_extract_noninitial_heading():
    chapter = Chapter(outline='Outline', content='Introduction\n# Later heading')

    assert chapter.title is None
    assert chapter.full_content == 'Introduction\n# Later heading'
    assert chapter.full_outline == 'Outline'


def test_full_content_requires_content():
    with pytest.raises(ValueError, match='chapter content is missing'):
        _ = Chapter(outline='Outline').full_content
