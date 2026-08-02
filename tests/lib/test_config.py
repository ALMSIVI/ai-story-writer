import json
import pytest

from pathlib import Path
from ai_story_writer.lib.config import GenerationConfigError, resolve_generation_config, resolve_model, resolve_template
from ai_story_writer.types import GenerationConfig, LlmModel


def test_resolve_generation_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    project_config = tmp_path / 'config'
    project_config.mkdir()
    with open(project_config / 'config.json', 'wt') as f:
        json.dump(
            {
                'model': 'project.model',
                'templates': {
                    'write': 'project-write',
                    'rewrite': 'project-rewrite',
                },
                'includeFullConversation': False,
                'fullChapterCount': 4,
            },
            f,
        )

    story_directory = tmp_path / 'stories'
    story_directory.mkdir()
    story_file = story_directory / 'story.yaml'
    with open(story_directory / 'config.json', 'wt') as f:
        json.dump(
            {
                'templates': {
                    'write': 'directory-write',
                },
                'includeFullConversation': True,
                'fullChapterCount': 3,
            },
            f,
        )

    explicit_config = tmp_path / 'custom.json'
    with open(explicit_config, 'wt') as f:
        json.dump({'model': 'explicit.model'}, f)

    generation_config = GenerationConfig(
        templates={'rewrite': 'story-rewrite'},
        includeFullConversation=False,
        fullChapterCount=2,
    )

    config = resolve_generation_config(story_file, generation_config, str(explicit_config))

    assert config.model == 'explicit.model'
    assert config.templates == {'write': 'directory-write', 'rewrite': 'story-rewrite'}
    assert config.include_full_conversation is False
    assert config.full_chapter_count == 2


def test_resolve_generation_config_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    project_config = tmp_path / 'config'
    project_config.mkdir()
    with open(project_config / 'config.json', 'wt') as f:
        json.dump(
            {
                'model': 'project.model',
                'templates': {
                    'write': 'project-write',
                    'rewrite': 'project-rewrite',
                },
            },
            f,
        )

    story_directory = tmp_path / 'stories'
    story_directory.mkdir()
    config = resolve_generation_config(story_directory / 'story.yaml')

    assert config.model == 'project.model'
    assert config.templates == {'write': 'project-write', 'rewrite': 'project-rewrite'}
    assert config.include_full_conversation is False
    assert config.full_chapter_count is None


def test_resolve_generation_config_skips_missing_implicit_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)
    generation_config = GenerationConfig(templates={'write': 'story-write'})

    config = resolve_generation_config(tmp_path / 'story.yaml', generation_config)

    assert config.model is None
    assert config.templates == {'write': 'story-write'}
    assert config.include_full_conversation is False
    assert config.full_chapter_count is None


def test_resolve_generation_config_requires_explicit_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(GenerationConfigError, match='does not exist'):
        resolve_generation_config(tmp_path / 'story.yaml', config_file='missing.json')


def test_resolve_model():
    assert resolve_model(GenerationConfig(model='Provider.model')) == LlmModel(
        provider='Provider',
        name='model',
    )


def test_resolve_model_optional():
    assert resolve_model(GenerationConfig()) is None


def test_resolve_model_reports_invalid_value():
    with pytest.raises(GenerationConfigError, match='Failed to parse model invalid'):
        resolve_model(GenerationConfig(model='invalid'))


def test_resolve_template():
    config = GenerationConfig(templates={'write': 'write-prompt', 'rewrite': 'rewrite-prompt'})

    assert resolve_template(config, 'rewrite') == 'rewrite-prompt'


def test_resolve_template_requires_operation():
    config = GenerationConfig(templates={'write': 'write-prompt'})

    with pytest.raises(GenerationConfigError, match='No template configured for rewrite'):
        resolve_template(config, 'rewrite')
