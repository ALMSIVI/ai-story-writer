from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

from ai_story_writer.commands.write import _apply_completion, _create_prompt
from ai_story_writer.lib import prompt as prompt_module
from ai_story_writer.lib.story_document import YamlStoryDocument
from ai_story_writer.types import Background, Chapter, GenerationCompletedEvent, Story


@pytest.mark.parametrize('background', [None, [], ['World overview', 'Knowledge\nPrinciples']])
def test_prompt_renders_background_entries(background: list[str] | None, template_environment: Environment):
    template_environment.loader = FileSystemLoader('config/defaults/templates')
    story = Story(title='Story', background=background, chapters=[Chapter(outline='First')])

    # Use the default section with an isolated composition.
    (prompt_module.prompts_path / 'background.json').write_text(
        '{"sections": [{"name": "story-background"}, {"name": "current-chapter-task"}]}'
    )
    prompt = _create_prompt(story, 0, 'background', None)

    if background:
        assert '\n\n'.join(background) in prompt
        assert str(background) not in prompt
    else:
        assert '<background_information>' not in prompt


def test_completion_preserves_background(tmp_path: Path):
    story = Story(
        title='Story',
        background=['World'],
        chapters=[Chapter(outline='First', background=['Chapter setting'])],
    )
    document = YamlStoryDocument.from_story(story)
    yaml_file = tmp_path / 'story.yaml'

    _apply_completion(document, yaml_file, 0, GenerationCompletedEvent(content='# Title\n\nBody'))

    restored = YamlStoryDocument.load_files(yaml_file)
    assert restored.story.background == [Background(content='World')]
    assert restored.story.chapters[0].background == [Background(content='Chapter setting')]
    assert restored.story.chapters[0].full_content == '# Title\n\nBody'


def test_prompt_includes_only_matching_background_content(template_environment: Environment):
    template_environment.loader = FileSystemLoader('config/defaults/templates')
    (prompt_module.prompts_path / 'background.json').write_text(
        '{"sections": [{"name": "story-background"}, {"name": "current-chapter-task"}]}'
    )
    story = Story.model_validate(
        {
            'title': 'Story',
            'background': [
                'General facts',
                {'keywords': ['gate'], 'content': 'Gate rules'},
                {'keywords': ['forest'], 'content': 'Forest rules'},
            ],
            'chapters': [
                {'outline': 'First', 'background': [{'keywords': ['gate'], 'content': 'Local gate details'}]},
                {'outline': 'The GATE opens'},
            ],
        }
    )

    prompt = _create_prompt(story, 1, 'background', 0)

    assert 'General facts\n\nGate rules\n\nLocal gate details' in prompt
    assert 'Forest rules' not in prompt
    assert 'keywords' not in prompt
    assert 'Background(' not in prompt


@pytest.mark.parametrize('composition', ['write', 'write-full'])
def test_default_prompt_filters_and_renders_characters(
    composition: str, template_environment: Environment, monkeypatch
):
    template_environment.loader = FileSystemLoader('config/defaults/templates')
    monkeypatch.setattr(prompt_module, 'prompts_path', Path('config/defaults/prompts'))
    story = Story.model_validate(
        {
            'title': 'Story',
            'characters': [
                {'name': 'Narrator', 'content': 'Always present'},
                {'name': 'Mara', 'keywords': ['Red Fox', 'captain'], 'content': 'A resourceful sailor'},
                {'name': 'Guard', 'keywords': ['guard'], 'content': 'Only in another chapter'},
                {'name': 'Hidden', 'keywords': [], 'content': 'Never included'},
            ],
            'chapters': [{'outline': 'The guard waits'}, {'outline': 'The CAPTAIN arrives'}],
        }
    )

    rendered = _create_prompt(story, 1, composition, 0)

    assert '#### Narrator\n\nAlways present' in rendered
    assert '#### Mara\n\nA resourceful sailor' in rendered
    assert rendered.count('A resourceful sailor') == 1
    assert 'Only in another chapter' not in rendered
    assert 'Never included' not in rendered
    assert 'keywords' not in rendered


@pytest.mark.parametrize('characters', [None, []])
def test_prompt_omits_empty_character_section(characters, template_environment: Environment, monkeypatch):
    template_environment.loader = FileSystemLoader('config/defaults/templates')
    monkeypatch.setattr(prompt_module, 'prompts_path', Path('config/defaults/prompts'))
    story = Story(title='Story', characters=characters, chapters=[Chapter(outline='First')])

    assert '### Characters' not in _create_prompt(story, 0, 'write', None)
