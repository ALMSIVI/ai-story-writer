from argparse import ArgumentParser, Namespace
from functools import partial
from pathlib import Path
from uuid import uuid4

from ai_story_writer.lib.story import generate_id, find_chapter_index
from ai_story_writer.lib.config import resolve_generation_config, resolve_model, resolve_template
from ai_story_writer.lib.generation import (
    run_generation,
)
from ai_story_writer.lib.messages import create_messages
from ai_story_writer.lib.story_document import YamlStoryDocument
from ai_story_writer.types import (
    Chapter,
    GenerationCompletedEvent,
)


def register(parser: ArgumentParser):
    parser.add_argument('file', help='YAML story instruction file')
    parser.add_argument(
        '-i',
        '--id',
        default=None,
        help='ID of chapter to write a fresh version of; leave blank to write the first chapter without an ID',
    )
    parser.add_argument('-c', '--config', help='JSON configuration file')
    parser.add_argument(
        '-d',
        '--dry-run',
        action='store_true',
        help='Print the full prompt and, when a model is configured, its input token count',
    )
    parser.set_defaults(func=write)


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


def write(args: Namespace):
    yaml_file = Path(args.file)
    story_document = YamlStoryDocument.load_files(yaml_file)
    config = resolve_generation_config(yaml_file, story_document.generation_config, args.config)
    template = resolve_template(config, 'write')
    model = resolve_model(config)

    if story_document.story.id is None:
        story_document.set_story_id(str(uuid4()))

    chapter_index = find_chapter_index(story_document.story, args.id)
    messages = create_messages(
        story_document.story, chapter_index, template, config.include_full_conversation, config.full_chapter_count
    )

    apply_completion = partial(_apply_completion, story_document, yaml_file, chapter_index)
    run_generation(messages, model, apply_completion, dry_run=args.dry_run)
