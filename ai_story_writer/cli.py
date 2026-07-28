from argparse import ArgumentParser

from ai_story_writer.commands import CommandError
from ai_story_writer.commands.generate import register as register_generate
from ai_story_writer.lib.config import GenerationConfigError
from ai_story_writer.lib.prompt import PromptTemplateError
from ai_story_writer.lib.yaml import StoryFileError


parser = ArgumentParser()
subparsers = parser.add_subparsers(help='Tools provided by this package.', dest='command', required=True)
generate_parser = subparsers.add_parser('generate', description='Generates a chapter.')
register_generate(generate_parser)


def start():
    args = parser.parse_args()
    try:
        args.func(args)
    except (CommandError, GenerationConfigError, PromptTemplateError, StoryFileError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    start()
