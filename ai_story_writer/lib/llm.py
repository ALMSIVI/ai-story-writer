from pathlib import Path
from typing import Iterator
from uuid import UUID, uuid4
from ai_story_writer.clients import LlmClient, AnthropicClient, GoogleClient, OpenAIClient
from ai_story_writer.types import (
    Chapter,
    ModelConfig,
    LlmModel,
    Story,
    GenerationEvent,
    StartGenerationEvent,
    GenerationInProgressEvent,
    GenerationCompletedEvent,
    GenerationErrorEvent,
)

templates_path = Path('config', 'templates')
clients: dict[str, LlmClient] = {}
generations: set[UUID] = set()


def __create_generation_id():
    while True:
        id = uuid4()
        if id not in generations:
            generations.add(id)
            return id


def add_client(provider: str, model_config: ModelConfig):
    included_models = set(model_config.included_models if model_config.included_models is not None else [])
    match provider:
        case 'Anthropic':
            clients[provider] = AnthropicClient(model_config.api_key, included_models)
        case 'Google':
            clients[provider] = GoogleClient(model_config.api_key, included_models)
        case _:
            clients[provider] = OpenAIClient(model_config.api_key, included_models, provider, model_config.base_url)


def get_llm_models() -> list[LlmModel]:
    models: list[LlmModel] = []
    for client in clients.values():
        models += client.list_models()
    return models


def create_prompt(
    story: Story,
    current_outline: str,
    previous_chapters: list[Chapter] | None,
    next_outline: str | None,
    lore: str,
) -> str:
    template_name = story.template if story.template is not None else 'default'
    template_path = templates_path / f'{template_name}.md'
    with template_path.open() as f:
        template = f.read()

    if previous_chapters is None:
        previous_chapters = []
    previous_contents = '\n'.join([chapter.content for chapter in previous_chapters])
    if next_outline is None:
        next_outline = ''

    return (
        template.replace('{{lore}}', lore)
        .replace('{{previous}}', previous_contents)
        .replace('{{current}}', current_outline)
        .replace('{{next}}', next_outline)
    )


def generate_chapter(
    story: Story,
    lore: str,
    currrent_outline: str,
    previous_chapters: list[Chapter] | None,
    next_outline: str | None,
) -> Iterator[GenerationEvent]:
    prompt = create_prompt(story, currrent_outline, previous_chapters, next_outline, lore)
    model = story.model
    if model.provider not in clients:
        raise ValueError(f'client {model.provider} does not exist')

    try:
        generation = clients[model.provider].generate(prompt, model.name)
        generation_id = __create_generation_id()
        content = ''
        yield StartGenerationEvent(id=str(generation_id))
        for chunk in generation:
            if generation_id not in generations:
                return GenerationCompletedEvent(interrupted=True, content=content)

            content += chunk
            yield GenerationInProgressEvent(chunk=chunk)

        yield GenerationCompletedEvent(interrupted=False, content=content)
        generations.remove(generation_id)
    except Exception as e:
        return GenerationErrorEvent(message=str(e))
