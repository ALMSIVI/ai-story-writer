from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateError
from pydantic import ValidationError

from ai_story_writer.types import PromptTemplate


prompts_path = Path('config', 'prompts')
templates_path = Path('config', 'templates')
jinja_env = Environment(loader=FileSystemLoader(templates_path))



class PromptTemplateError(ValueError):
    pass


def _load_prompt_template(name: str) -> PromptTemplate:
    path = prompts_path / f'{name}.json'
    try:
        document = path.read_text()
    except FileNotFoundError:
        raise PromptTemplateError(f'Prompt template does not exist: {path}') from None
    except OSError as error:
        raise PromptTemplateError(f'Failed to read prompt template {path}: {error}') from error

    try:
        return PromptTemplate.model_validate_json(document)
    except ValidationError as error:
        raise PromptTemplateError(f'Invalid prompt template in {path}: {error}') from error


def render_prompt(name: str, context: Mapping[str, Any]) -> str:
    prompt_template = _load_prompt_template(name)
    rendered_sections: list[str] = []

    for section in prompt_template.sections:
        if not section.enabled:
            continue

        template_name = f'{section.name}.jinja'
        try:
            rendered = jinja_env.get_template(template_name).render(**context).strip()
        except TemplateError as error:
            raise PromptTemplateError(f'Failed to render prompt section {template_name}: {error}') from error
        if rendered:
            rendered_sections.append(rendered)

    if not rendered_sections:
        raise PromptTemplateError(f'Prompt template {name} rendered no content')
    return '\n\n'.join(rendered_sections)
