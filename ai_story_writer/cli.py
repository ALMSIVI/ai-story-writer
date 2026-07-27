import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from uuid import uuid4
from ai_story_writer.lib.llm import count_input_tokens, create_messages, generate_chapter
from ai_story_writer.setup import teardown, setup
from ai_story_writer.types import (
    Chapter,
    GenerationCompletedEvent,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
)
from ai_story_writer.utils.config import GenerationConfigError, resolve_generation_config
from ai_story_writer.utils.id import generate_id
from ai_story_writer.utils.markdown import dump_markdown
from ai_story_writer.utils.yaml import StoryFileError, YamlStoryDocument


class CliError(ValueError):
    pass


def generate(args: Namespace):
    yaml_file = Path(args.file)
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
    config = resolve_generation_config(yaml_file, story_document.generation_config, args.config)
    if config.template is None:
        raise CliError('No template configured')
    if config.model is None:
        if not args.dry_run:
            raise CliError('No model configured')
        model = None
    else:
        try:
            model = LlmModel.parse(config.model)
        except ValueError as error:
            raise CliError(str(error)) from error

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
            config.template,
            include_full_conversation=config.include_full_conversation,
            full_chapter_count=config.full_chapter_count,
        )
        if len(messages) == 1:
            print(messages[0].content)
        else:
            print('\n\n'.join(f'[{message.role.value}]\n{message.content}' for message in messages))

        if model is not None:
            try:
                setup()
                input_tokens = count_input_tokens(messages, model)
                if input_tokens is not None:
                    print(f'Input tokens: {input_tokens}')
            finally:
                teardown()
        return

    try:
        setup()
        for event in generate_chapter(
            story,
            index,
            model,
            config.template,
            include_full_conversation=config.include_full_conversation,
            full_chapter_count=config.full_chapter_count,
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
    finally:
        teardown()


parser = ArgumentParser()
subparsers = parser.add_subparsers(help='Tools provided by this package.', dest='command', required=True)

generate_parser = subparsers.add_parser('generate', description='Generates a chapter.')
generate_parser.add_argument('file', help='YAML story instruction file')
generate_parser.add_argument(
    '-i', '--id', default=None, help='ID of chapter to regenerate, leave blank to generate first chapter without ID'
)
generate_parser.add_argument('-c', '--config', help='JSON configuration file')
generate_parser.add_argument(
    '-d',
    '--dry-run',
    action='store_true',
    help='Print the full prompt and, when a model is configured, its input token count',
)
generate_parser.set_defaults(func=generate)


def start():
    args = parser.parse_args()
    try:
        args.func(args)
    except (CliError, GenerationConfigError, StoryFileError) as error:
        parser.error(str(error))


if __name__ == 'main':
    start()
