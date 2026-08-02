import json
from pathlib import Path

import pytest
from jinja2 import DictLoader, Environment

from ai_story_writer.lib import prompt
from ai_story_writer.lib.prompt import PromptTemplateError


def _configure_prompt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    document: object | None,
    templates: dict[str, str],
):
    prompts_path = tmp_path / 'prompts'
    prompts_path.mkdir()
    if document is not None:
        (prompts_path / 'test.json').write_text(json.dumps(document))
    monkeypatch.setattr(prompt, 'prompts_path', prompts_path)
    monkeypatch.setattr(prompt, 'jinja_env', Environment(loader=DictLoader(templates)))


def test_render_prompt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _configure_prompt(
        tmp_path,
        monkeypatch,
        {
            'sections': [
                {'name': 'first'},
                {'name': 'disabled', 'enabled': False},
                {'name': 'empty'},
                {'name': 'last', 'enabled': True},
            ]
        },
        {
            'first.jinja': '  Hello {{ name }}  ',
            'empty.jinja': '{% if missing %}not rendered{% endif %}',
            'last.jinja': '\nLast\n',
        },
    )

    assert prompt.render_prompt('test', {'name': 'Writer'}) == 'Hello Writer\n\nLast'


@pytest.mark.parametrize(
    ('name', 'document', 'templates', 'message'),
    [
        ('missing', None, {}, 'Prompt template does not exist'),
        ('test', {'sections': []}, {}, 'Invalid prompt template'),
        ('test', {'sections': [{'name': 'missing'}]}, {}, 'Failed to render prompt section missing.jinja'),
        ('test', {'sections': [{'name': 'empty'}]}, {'empty.jinja': ''}, 'rendered no content'),
        (
            'test',
            {'sections': [{'name': 'section'}]},
            {'section.jinja': '{% if missing %}'},
            'Failed to render prompt section section.jinja',
        ),
    ],
)
def test_render_prompt_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    document: object | None,
    templates: dict[str, str],
    message: str,
):
    _configure_prompt(tmp_path, monkeypatch, document, templates)

    with pytest.raises(PromptTemplateError, match=message):
        prompt.render_prompt(name, {})


def test_render_prompt_reports_malformed_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    prompts_path = tmp_path / 'prompts'
    prompts_path.mkdir()
    (prompts_path / 'test.json').write_text('{')
    monkeypatch.setattr(prompt, 'prompts_path', prompts_path)

    with pytest.raises(PromptTemplateError, match='Invalid prompt template'):
        prompt.render_prompt('test', {})
