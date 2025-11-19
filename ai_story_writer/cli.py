from argparse import ArgumentParser
from pathlib import Path
import sys
from uuid import uuid4
from ai_story_writer.setup import teardown, setup
from ai_story_writer.lib.llm import generate_chapter
from ai_story_writer.types import LlmModel, GenerationInProgressEvent, GenerationCompletedEvent, GenerationErrorEvent
from ai_story_writer.utils.cli import dump_story, parse_files
from ai_story_writer.utils.id import generate_id


parser = ArgumentParser()
parser.add_argument('-f', '--file', help='text file to store the story', required=True)
parser.add_argument(
    '-i', '--id', default=None, help='ID of chapter to regenerate, leave blank to generate first chapter without ID'
)
parser.add_argument('-m', '--model', help='Model used to generate', required=True)
parser.add_argument('-t', '--template', default='default', help='Template for prompt')
parser.add_argument('-c', '--convo', action='store_true', help='Include full conversation for generation')


def start():
    setup()
    args = parser.parse_args()

    txt_file = Path(args.file)
    md_file = txt_file.with_suffix('.md')

    id = args.id
    with txt_file.open() as f:
        txt_str = f.read()

    if md_file.exists():
        with md_file.open() as f:
            md_str = f.read()
    else:
        md_str = ''

    cli_story = parse_files(txt_str, md_str)

    if cli_story.id is None:
        cli_story.id = str(uuid4())

    all_chapters = cli_story.chapters

    if id is None:
        # Generate first chapter without id
        try:
            index = next(i for i, c in enumerate(all_chapters) if c.id is None)
        except StopIteration:
            raise KeyError('Cannot find chapter without id')
    else:
        # Regenerate chapter with id
        try:
            index = next(i for i, c in enumerate(all_chapters) if c.id == id)
        except StopIteration:
            raise KeyError(f'Cannot find chapter with id {id}')

    previous_chapters = all_chapters[:index]
    current_chapter = all_chapters[index]
    lore = current_chapter.lore
    if lore is None:
        for chapter in reversed(previous_chapters):
            if chapter.lore is not None:
                lore = chapter.lore
                break

    next_outline = None
    if index < len(all_chapters) - 1:
        next_outline = all_chapters[index + 1].outline

    cli_story.chapters = previous_chapters
    story, chapters = cli_story.to_story_chapters(LlmModel.parse(args.model), args.template)

    for event in generate_chapter(story, lore, current_chapter.outline, chapters, next_outline, args.convo):
        if isinstance(event, GenerationInProgressEvent):
            print(event.chunk, end='', flush=True)
        elif isinstance(event, GenerationCompletedEvent):
            content: str = event.content
            current_chapter.content = content
            if current_chapter.id is None:
                current_chapter.id = generate_id(chapters)
            cli_story.chapters = all_chapters
            txt_str, md_str = dump_story(cli_story)
            with txt_file.open('wt') as f:
                f.write(txt_str)
            with md_file.open('wt') as f:
                f.write(md_str)
        elif isinstance(event, GenerationErrorEvent):
            print(f'Encountered error {event.message}', file=sys.stderr)

if __name__ == 'main':
    try:
        start()
    finally:
        teardown()
