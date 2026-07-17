from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Iterator
from ai_story_writer.clients import LlmClient, AnthropicClient, GoogleClient, OpenAIClient, OllamaClient
from ai_story_writer.types import (
    Chapter,
    LlmModel,
    Message,
    ModelConfig,
    Role,
    Story,
    GenerationEvent,
    GenerationInProgressEvent,
    GenerationCompletedEvent,
    GenerationErrorEvent,
)

templates_path = Path('config', 'templates')
jinja_env = Environment(loader=FileSystemLoader(templates_path))
clients: dict[str, LlmClient] = {}


def add_client(provider: str, model_config: ModelConfig):
    supported_models = set(model_config.supported_models if model_config.supported_models is not None else [])
    match provider:
        case 'Anthropic':
            clients[provider] = AnthropicClient(model_config.api_key, supported_models)
        case 'Google':
            clients[provider] = GoogleClient(model_config.api_key, supported_models)
        case 'Ollama':
            clients[provider] = OllamaClient(
                api_key=model_config.api_key,
                supported_models=supported_models,
                provider=provider,
                base_url=model_config.base_url,
            )
        case _:
            sdk = model_config.base_sdk
            match sdk:
                case 'Anthropic':
                    clients[provider] = AnthropicClient(
                        model_config.api_key, supported_models, provider, model_config.base_url
                    )
                case _:
                    clients[provider] = OpenAIClient(
                        model_config.api_key, supported_models, provider, model_config.base_url
                    )


def cleanup_clients():
    for client in clients.values():
        client.close()
    clients.clear()


def __create_prompt(
    story: Story,
    template: str,
    lore: str,
    current_outline: str,
    previous_chapters: list[Chapter] | None,
    next_outline: str | None,
) -> str:
    template_name = f'{template}.jinja'
    template = jinja_env.get_template(template_name)

    if previous_chapters is None:
        previous_chapters = []

    if story.chapter_count is not None and len(previous_chapters) > story.chapter_count:
        summary_length = len(previous_chapters) - story.chapter_count
        summary = '\n\n'.join([chapter.full_outline for chapter in previous_chapters[:summary_length]])
        previous_contents = '\n\n'.join([chapter.full_content for chapter in previous_chapters[summary_length:]])
    else:
        summary = None
        previous_contents = '\n\n'.join([chapter.full_content for chapter in previous_chapters])
    if next_outline is None:
        next_outline = ''

    return template.render(
        title=story.title,
        style=story.style,
        lore=lore,
        summary=summary,
        previous=previous_contents,
        current=current_outline,
        next=next_outline,
    )


def __create_history(
    story: Story,
    template: str,
    lore: str,
    current_outline: str,
    previous_chapters: list[Chapter] | None,
) -> list[Message]:
    template_name = f'{template}.jinja'
    template = jinja_env.get_template(template_name)
    system_message = template.render(
        title=story.title,
        style=story.style,
        lore=lore,
    )

    messages = [Message(role=Role.SYSTEM, content=system_message)]

    if previous_chapters is None:
        previous_chapters = []

    for chapter in previous_chapters:
        if chapter.content is None:
            raise ValueError(f'chapter {chapter.id or chapter.outline!r} content is missing')
        messages.append(Message(role=Role.USER, content=chapter.outline))
        messages.append(Message(role=Role.ASSISTANT, content=chapter.content))

    messages.append(Message(role=Role.USER, content=current_outline))
    return messages


def generate_chapter(
    story: Story,
    model: LlmModel,
    template: str,
    lore: str,
    current_outline: str,
    previous_chapters: list[Chapter] | None,
    next_outline: str | None,
    include_full_convo: bool = False,
) -> Iterator[GenerationEvent]:
    if include_full_convo:
        messages = __create_history(story, template, lore, current_outline, previous_chapters)
    else:
        prompt = __create_prompt(story, template, lore, current_outline, previous_chapters, next_outline)
        messages = [Message(role=Role.USER, content=prompt)]
    if model.provider not in clients:
        raise ValueError(f'client {model.provider} does not exist')

    client = clients[model.provider]
    if model.name not in client.supported_models:
        raise ValueError(f'model {model.name} not supported in client {model.provider}')

    try:
        generation = clients[model.provider].generate(messages, model.name)
        content = ''
        for chunk in generation:
            content += chunk
            yield GenerationInProgressEvent(chunk=chunk)

        yield GenerationCompletedEvent(content=content)
    except Exception as e:
        yield GenerationErrorEvent(message=str(e))
