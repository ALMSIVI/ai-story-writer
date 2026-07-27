import pytest

from ai_story_writer.lib.markdown import dump_markdown, parse_markdown
from ai_story_writer.types import Chapter, Story


@pytest.mark.parametrize(
    ('md_str', 'sections'),
    [
        ('', []),
        ('Untitled body\n\n## Subheading\n\nMore', ['Untitled body\n\n## Subheading\n\nMore']),
        (
            '# First\n\nBody\n\n## Subheading\n\nMore\n\n# Second\n\nEnding',
            ['# First\n\nBody\n\n## Subheading\n\nMore', '# Second\n\nEnding'],
        ),
    ],
)
def test_parse_markdown(md_str: str, sections: list[str]):
    assert parse_markdown(md_str) == sections


def test_dump_markdown():
    story = Story(
        title='Story',
        chapters=[
            Chapter(outline='First outline', content='# First\n\nBody\n\n## Subheading\n\nMore'),
            Chapter(outline='Pending outline'),
            Chapter(outline='Third outline', content='Untitled ending'),
        ],
    )

    assert dump_markdown(story) == '# First\n\nBody\n\n## Subheading\n\nMore\n\nUntitled ending'


def test_dump_markdown_without_generated_content():
    story = Story(title='Story', chapters=[Chapter(outline='Pending outline')])

    assert dump_markdown(story) == ''
