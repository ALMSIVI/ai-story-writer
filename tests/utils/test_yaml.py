import pytest

from ai_story_writer.types import Chapter, Story
from ai_story_writer.utils.yaml import StoryFileError, YamlStoryDocument


def test_yaml_story_round_trip():
    yaml_str = """\
title: Story
style: |-
  Lyrical
  Restrained
chapter_count: 2
chapters:
  - id: first
    lore: |-
      Shared lore
      Second line
    outline: |-
      First beat

      A heading follows:
      # Not a YAML comment
  - outline: |-
      Text containing ---
"""
    md_str = '# First\n\nBody\n\n## Section\n\nMore'

    story = YamlStoryDocument.load(yaml_str, md_str).story

    assert story == Story(
        title='Story',
        style='Lyrical\nRestrained',
        chapter_count=2,
        chapters=[
            Chapter(
                id='first',
                lore='Shared lore\nSecond line',
                outline='First beat\n\nA heading follows:\n# Not a YAML comment',
                content='# First\n\nBody\n\n## Section\n\nMore',
            ),
            Chapter(outline='Text containing ---'),
        ],
    )


def test_adding_ids():
    yaml_str = """\
# User comment
title: Story
style: |-
  Lyrical
  Restrained
chapters:
  - lore: |-
      Shared lore
    outline: |-
      First beat

      Second beat
"""
    document = YamlStoryDocument.load(yaml_str)

    document.set_story_id('story-id')
    document.set_chapter_id(0, 'chapter-id')

    assert (
        document.dump()
        == """\
# User comment
id: story-id
title: Story
style: |-
  Lyrical
  Restrained
chapters:
  - id: chapter-id
    lore: |-
      Shared lore
    outline: |-
      First beat

      Second beat
"""
    )


def test_from_story():
    document = YamlStoryDocument.from_story(
        Story(
            title='Story',
            style='One line',
            chapters=[Chapter(lore='Lore\nSecond line', outline='Outline\n\nSecond beat')],
        )
    )

    assert (
        document.dump()
        == """\
title: Story
style: |-
  One line
chapters:
  - lore: |-
      Lore
      Second line
    outline: |-
      Outline

      Second beat
"""
    )


@pytest.mark.parametrize(
    ('yaml_str', 'message'),
    [
        ('- title: Story', 'top-level mapping'),
        ('title: Story\nunknown: value\nchapters: []', 'Extra inputs are not permitted'),
        ('title: Story\nchapters:\n  - outline: Outline\n    content: Body', 'Extra inputs are not permitted'),
        ('title: Story\nchapters:\n  - lore: Lore', 'Field required'),
    ],
)
def test_invalid_yaml_story(yaml_str: str, message: str):
    with pytest.raises(StoryFileError, match=message):
        YamlStoryDocument.load(yaml_str)
