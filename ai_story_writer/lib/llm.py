from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Iterator
from ai_story_writer.clients import LlmClient, AnthropicClient, GoogleClient, OpenAIClient, OllamaClient
from ai_story_writer.types import (
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


def _validate_chapter_index(story: Story, chapter_index: int):
    if chapter_index < 0 or chapter_index >= len(story.chapters):
        raise IndexError(f'chapter index {chapter_index} out of range')


def _get_lore(story: Story, chapter_index: int) -> str | None:
    for chapter in reversed(story.chapters[: chapter_index + 1]):
        if chapter.lore is not None:
            return chapter.lore
    return None


def _create_prompt(
    story: Story,
    chapter_index: int,
    template: str,
) -> str:
    template_name = f'{template}.jinja'
    jinja_template = jinja_env.get_template(template_name)

    previous_chapters = story.chapters[:chapter_index]
    current_chapter = story.chapters[chapter_index]

    if story.chapter_count is not None and len(previous_chapters) > story.chapter_count:
        summary_length = len(previous_chapters) - story.chapter_count
        summary = '\n\n'.join([chapter.full_outline for chapter in previous_chapters[:summary_length]])
        previous_contents = '\n\n'.join([chapter.full_content for chapter in previous_chapters[summary_length:]])
    else:
        summary = None
        previous_contents = '\n\n'.join([chapter.full_content for chapter in previous_chapters])

    next_outline = ''
    if chapter_index < len(story.chapters) - 1:
        next_outline = story.chapters[chapter_index + 1].outline

    return jinja_template.render(
        title=story.title,
        style=story.style,
        lore=_get_lore(story, chapter_index),
        summary=summary,
        previous=previous_contents,
        current=current_chapter.outline,
        next=next_outline,
    )


def _create_history(
    story: Story,
    chapter_index: int,
    template: str,
) -> list[Message]:
    template_name = f'{template}.jinja'
    jinja_template = jinja_env.get_template(template_name)
    system_message = jinja_template.render(
        title=story.title,
        style=story.style,
        lore=_get_lore(story, chapter_index),
    )

    messages = [Message(role=Role.SYSTEM, content=system_message)]

    for chapter in story.chapters[:chapter_index]:
        messages.append(Message(role=Role.USER, content=chapter.outline))
        messages.append(Message(role=Role.ASSISTANT, content=chapter.full_content))

    messages.append(Message(role=Role.USER, content=story.chapters[chapter_index].outline))
    return messages


def create_messages(
    story: Story,
    chapter_index: int,
    template: str,
    include_full_convo: bool = False,
) -> list[Message]:
    """Build the complete LLM input without contacting a provider."""
    _validate_chapter_index(story, chapter_index)

    if include_full_convo:
        return _create_history(story, chapter_index, template)

    prompt = _create_prompt(story, chapter_index, template)
    return [Message(role=Role.USER, content=prompt)]


def generate_chapter(
    story: Story,
    chapter_index: int,
    model: LlmModel,
    template: str,
    include_full_convo: bool = False,
) -> Iterator[GenerationEvent]:
    messages = create_messages(
        story,
        chapter_index,
        template,
        include_full_convo,
    )
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
