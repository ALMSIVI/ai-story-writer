from argparse import ArgumentParser, Namespace
from functools import partial
from pathlib import Path
from uuid import uuid4

from ai_story_writer.lib.story import (
    generate_id,
    find_chapter_index,
    get_background,
    get_instructions,
    get_characters,
    get_previous_context,
    get_next_outline,
)
from ai_story_writer.lib.config import resolve_generation_config, resolve_model, resolve_template
from ai_story_writer.lib.generation import (
    run_generation,
)
from ai_story_writer.lib.prompt import render_prompt
from ai_story_writer.lib.story_document import YamlStoryDocument
from ai_story_writer.types import (
    Chapter,
    GenerationCompletedEvent,
    Story,
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


def _create_prompt(
    story: Story,
    chapter_index: int,
    template: str,
    full_chapter_count: int | None,
):
    current_chapter = story.chapters[chapter_index]
    summary, previous_contents = get_previous_context(story, chapter_index, full_chapter_count)

    return render_prompt(
        template,
        {
            'title': story.title,
            'style': story.style,
            'background': get_background(story, chapter_index),
            'instructions': get_instructions(story, chapter_index),
            'characters': get_characters(story, chapter_index),
            'summary': summary,
            'previous': previous_contents,
            'current': current_chapter.outline,
            'next': get_next_outline(story, chapter_index),
        },
    )


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
        background=current_chapter.background,
        instructions=current_chapter.instructions,
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
    prompt = _create_prompt(story_document.story, chapter_index, template, config.full_chapter_count)

    apply_completion = partial(_apply_completion, story_document, yaml_file, chapter_index)
    run_generation(prompt, model, apply_completion, dry_run=args.dry_run)
