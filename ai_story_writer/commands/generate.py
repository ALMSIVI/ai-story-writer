import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from uuid import uuid4

from ai_story_writer.commands import CommandError
from ai_story_writer.lib.config import resolve_generation_config
from ai_story_writer.lib.id import generate_id
from ai_story_writer.lib.llm import count_input_tokens, create_messages, generate_chapter
from ai_story_writer.lib.yaml import YamlStoryDocument
from ai_story_writer.setup import setup, teardown
from ai_story_writer.types import (
    Chapter,
    GenerationCompletedEvent,
    GenerationConfig,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
    Message,
    Story,
)


def register(parser: ArgumentParser):
    parser.add_argument('file', help='YAML story instruction file')
    parser.add_argument(
        '-i',
        '--id',
        default=None,
        help='ID of chapter to regenerate, leave blank to generate first chapter without ID',
    )
    parser.add_argument('-c', '--config', help='JSON configuration file')
    parser.add_argument(
        '-d',
        '--dry-run',
        action='store_true',
        help='Print the full prompt and, when a model is configured, its input token count',
    )
    parser.set_defaults(func=generate)


def _resolve_model(config: GenerationConfig, dry_run: bool) -> LlmModel | None:
    if config.template is None:
        raise CommandError('No template configured')
    if config.model is None:
        if not dry_run:
            raise CommandError('No model configured')
        return None
    try:
        return LlmModel.parse(config.model)
    except ValueError as error:
        raise CommandError(str(error)) from error


def _find_chapter_index(story: Story, chapter_id: str | None) -> int:
    if chapter_id is None:
        try:
            return next(index for index, chapter in enumerate(story.chapters) if chapter.id is None)
        except StopIteration:
            raise KeyError('Cannot find chapter without id') from None

    try:
        return next(index for index, chapter in enumerate(story.chapters) if chapter.id == chapter_id)
    except StopIteration:
        raise KeyError(f'Cannot find chapter with id {chapter_id}') from None


def _print_messages(messages: list[Message]) -> None:
    if len(messages) == 1:
        print(messages[0].content)
    else:
        print('\n\n'.join(f'[{message.role.value}]\n{message.content}' for message in messages))


def _dry_run(
    story: Story,
    chapter_index: int,
    config: GenerationConfig,
    model: LlmModel | None,
):
    messages = create_messages(
        story,
        chapter_index,
        config.template,
        include_full_conversation=config.include_full_conversation,
        full_chapter_count=config.full_chapter_count,
    )
    _print_messages(messages)

    if model is None:
        return

    try:
        setup()
        input_tokens = count_input_tokens(messages, model)
        if input_tokens is not None:
            print(f'Input tokens: {input_tokens}')
    finally:
        teardown()


def _apply_completion(
    story_document: YamlStoryDocument,
    yaml_file: Path,
    chapter_index: int,
    event: GenerationCompletedEvent,
):
    story = story_document.story
    current_chapter = story.chapters[chapter_index]
    chapter_id = current_chapter.id or generate_id(story.chapters)
    story.chapters[chapter_index] = Chapter(
        id=chapter_id,
        lore=current_chapter.lore,
        outline=current_chapter.outline,
        content=event.content,
    )
    story_document.set_chapter_id(chapter_index, chapter_id)
    story_document.write_files(yaml_file)


def _generate(
    story_document: YamlStoryDocument,
    yaml_file: Path,
    chapter_index: int,
    config: GenerationConfig,
    model: LlmModel,
):
    try:
        setup()
        for event in generate_chapter(
            story_document.story,
            chapter_index,
            model,
            config.template,
            include_full_conversation=config.include_full_conversation,
            full_chapter_count=config.full_chapter_count,
        ):
            if isinstance(event, GenerationInProgressEvent):
                print(event.chunk, end='', flush=True)
            elif isinstance(event, GenerationCompletedEvent):
                _apply_completion(story_document, yaml_file, chapter_index, event)
            elif isinstance(event, GenerationErrorEvent):
                print(f'Encountered error {event.message}', file=sys.stderr)
    finally:
        teardown()


def generate(args: Namespace):
    yaml_file = Path(args.file)
    story_document = YamlStoryDocument.load_files(yaml_file)
    config = resolve_generation_config(yaml_file, story_document.generation_config, args.config)
    model = _resolve_model(config, args.dry_run)

    if story_document.story.id is None:
        story_document.set_story_id(str(uuid4()))

    chapter_index = _find_chapter_index(story_document.story, args.id)

    if args.dry_run:
        _dry_run(story_document.story, chapter_index, config, model)
        return

    if model is None:
        raise CommandError('No model configured')
    _generate(story_document, yaml_file, chapter_index, config, model)
