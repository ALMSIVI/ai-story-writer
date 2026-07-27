from pathlib import Path

import pytest

from ai_story_writer.types import GenerationConfig
from ai_story_writer.utils.config import GenerationConfigError, resolve_generation_config


def test_resolve_generation_config_merges_each_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    project_config = tmp_path / 'config'
    project_config.mkdir()
    (project_config / 'config.json').write_text(
        '{"model":"project.model","template":"project-template","includeFullConversation":false,"fullChapterCount":4}'
    )
    story_directory = tmp_path / 'stories'
    story_directory.mkdir()
    story_file = story_directory / 'story.yaml'
    (story_directory / 'config.json').write_text(
        '{"template":"directory-template","includeFullConversation":true,"fullChapterCount":3}'
    )
    explicit_config = tmp_path / 'custom.json'
    explicit_config.write_text('{"model":"explicit.model"}')
    generation_config = GenerationConfig(includeFullConversation=False, fullChapterCount=2)

    config = resolve_generation_config(story_file, generation_config, str(explicit_config))

    assert config.model == 'explicit.model'
    assert config.template == 'directory-template'
    assert config.include_full_conversation is False
    assert config.full_chapter_count == 2


def test_resolve_generation_config_uses_project_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    project_config = tmp_path / 'config'
    project_config.mkdir()
    (project_config / 'config.json').write_text('{"model":"project.model","template":"project-template"}')
    story_directory = tmp_path / 'stories'
    story_directory.mkdir()
    config = resolve_generation_config(story_directory / 'story.yaml')

    assert config.model == 'project.model'
    assert config.template == 'project-template'
    assert config.include_full_conversation is False
    assert config.full_chapter_count is None


def test_resolve_generation_config_skips_missing_implicit_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)
    generation_config = GenerationConfig(template='story-template')

    config = resolve_generation_config(tmp_path / 'story.yaml', generation_config)

    assert config.model is None
    assert config.template == 'story-template'
    assert config.include_full_conversation is False
    assert config.full_chapter_count is None


def test_resolve_generation_config_requires_explicit_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(GenerationConfigError, match='does not exist'):
        resolve_generation_config(tmp_path / 'story.yaml', config_file='missing.json')
