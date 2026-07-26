import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from uuid import uuid4
from ai_story_writer.lib.llm import count_input_tokens, create_messages, generate_chapter
from ai_story_writer.setup import teardown, setup
from ai_story_writer.types import (
    Chapter,
    LlmModel,
    GenerationInProgressEvent,
    GenerationCompletedEvent,
    GenerationErrorEvent,
)
from ai_story_writer.utils.cli import dump_markdown, parse_files
from ai_story_writer.utils.id import generate_id
from ai_story_writer.utils.yaml import StoryFileError, YamlStoryDocument


class CliError(ValueError):
    pass


def _require_suffix(path: Path, suffix: str, description: str) -> None:
    if path.suffix != suffix:
        raise CliError(f'{description} must use the {suffix} extension: {path}')


def generate(args: Namespace):
    yaml_file = Path(args.file)
    _require_suffix(yaml_file, '.yaml', 'Story instruction file')
    md_file = yaml_file.with_suffix('.md')

    with yaml_file.open() as f:
        yaml_str = f.read()

    if md_file.exists():
        with md_file.open() as f:
            md_str = f.read()
    else:
        md_str = ''

    story_document = YamlStoryDocument.load(yaml_str, md_str)
    story = story_document.story

    if story.id is None:
        story_document.set_story_id(str(uuid4()))

    id = args.id
    if id is None:
        # Generate first chapter without id
        try:
            index = next(i for i, c in enumerate(story.chapters) if c.id is None)
        except StopIteration:
            raise KeyError('Cannot find chapter without id')
    else:
        # Regenerate chapter with id
        try:
            index = next(i for i, c in enumerate(story.chapters) if c.id == id)
        except StopIteration:
            raise KeyError(f'Cannot find chapter with id {id}')

    if args.dry_run:
        messages = create_messages(
            story,
            index,
            args.template,
            args.convo,
        )
        if len(messages) == 1:
            print(messages[0].content)
        else:
            print('\n\n'.join(f'[{message.role.value}]\n{message.content}' for message in messages))

        if args.model is not None:
            input_tokens = count_input_tokens(messages, LlmModel.parse(args.model))
            if input_tokens is not None:
                print(f'Input tokens: {input_tokens}')
        return

    model = LlmModel.parse(args.model)
    for event in generate_chapter(
        story,
        index,
        model,
        args.template,
        args.convo,
    ):
        if isinstance(event, GenerationInProgressEvent):
            print(event.chunk, end='', flush=True)
        elif isinstance(event, GenerationCompletedEvent):
            current_chapter = story.chapters[index]
            chapter_id = current_chapter.id or generate_id(story.chapters)
            story.chapters[index] = Chapter(
                id=chapter_id,
                lore=current_chapter.lore,
                outline=current_chapter.outline,
                content=event.content,
            )
            story_document.set_chapter_id(index, chapter_id)
            yaml_str = story_document.dump()
            md_str = dump_markdown(story)
            with yaml_file.open('wt') as f:
                f.write(yaml_str)
            with md_file.open('wt') as f:
                f.write(md_str)
        elif isinstance(event, GenerationErrorEvent):
            print(f'Encountered error {event.message}', file=sys.stderr)


def migrate(args: Namespace):
    txt_file = Path(args.file)
    _require_suffix(txt_file, '.txt', 'Legacy story instruction file')
    yaml_file = txt_file.with_suffix('.yaml')

    if yaml_file.exists():
        raise CliError(f'Refusing to overwrite existing YAML file: {yaml_file}')

    try:
        with txt_file.open() as f:
            txt_str = f.read()
        story = parse_files(txt_str, '')
        yaml_str = YamlStoryDocument.from_story(story).dump()
        with yaml_file.open('x') as f:
            f.write(yaml_str)
    except FileExistsError as error:
        raise CliError(f'Refusing to overwrite existing YAML file: {yaml_file}') from error
    except (OSError, ValueError) as error:
        if isinstance(error, CliError):
            raise
        raise CliError(f'Could not migrate {txt_file}: {error}') from error

    print(f'Migrated {txt_file} to {yaml_file}')


parser = ArgumentParser()
subparsers = parser.add_subparsers(help='Tools provided by this package.', dest='command', required=True)

generate_parser = subparsers.add_parser('generate', description='Generates a chapter.')
generate_parser.add_argument('-f', '--file', help='YAML story instruction file', required=True)
generate_parser.add_argument(
    '-i', '--id', default=None, help='ID of chapter to regenerate, leave blank to generate first chapter without ID'
)
generate_parser.add_argument(
    '-m',
    '--model',
    help='Model used to generate, or to count input tokens in a dry run (required unless --dry-run is used)',
)
generate_parser.add_argument('-t', '--template', default='default', help='Template for prompt')
generate_parser.add_argument('-c', '--convo', action='store_true', help='Include full conversation for generation')
generate_parser.add_argument(
    '--dry-run', action='store_true', help='Print the full prompt and, when --model is provided, its input token count'
)
generate_parser.set_defaults(func=generate)

migrate_parser = subparsers.add_parser('migrate', description='Migrates a legacy TXT story to YAML.')
migrate_parser.add_argument('-f', '--file', help='legacy TXT story instruction file', required=True)
migrate_parser.set_defaults(func=migrate)


def start():
    args = parser.parse_args()
    if args.command == 'generate':
        if not args.dry_run and args.model is None:
            parser.error('the following arguments are required: -m/--model')

        try:
            _require_suffix(Path(args.file), '.yaml', 'Story instruction file')
        except CliError as error:
            parser.error(f'{error}. Migrate legacy TXT files with: cli migrate --file story.txt')

    requires_setup = args.command == 'generate' and (not args.dry_run or args.model is not None)
    try:
        if requires_setup:
            setup()
        args.func(args)
    except (CliError, StoryFileError) as error:
        parser.error(str(error))
    finally:
        if requires_setup:
            teardown()


if __name__ == 'main':
    start()
