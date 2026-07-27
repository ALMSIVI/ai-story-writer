import pytest

from ai_story_writer.types import Chapter, GenerationConfig, Story
from ai_story_writer.utils.yaml import StoryFileError, YamlStoryDocument


def test_yaml_story_round_trip():
    yaml_str = """\
title: Story
style: |-
  Lyrical
  Restrained
config:
  model: OpenAI.gpt-5
  template: default
  includeFullConversation: true
  fullChapterCount: 2
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

    document = YamlStoryDocument.load(yaml_str, md_str)
    story = document.story

    assert story == Story(
        title='Story',
        style='Lyrical\nRestrained',
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
    assert document.generation_config == GenerationConfig(
        model='OpenAI.gpt-5',
        template='default',
        includeFullConversation=True,
        fullChapterCount=2,
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
        ),
        GenerationConfig(
            model='OpenAI.gpt-5',
            template='default',
            includeFullConversation=False,
            fullChapterCount=2,
        ),
    )

    assert (
        document.dump()
        == """\
title: Story
style: |-
  One line
config:
  model: OpenAI.gpt-5
  template: default
  includeFullConversation: false
  fullChapterCount: 2
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
