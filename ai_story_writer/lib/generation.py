import sys
from collections.abc import Callable

from ai_story_writer.lib.config import GenerationConfigError
from ai_story_writer.lib.llm import cleanup_clients, count_input_tokens, generate, initialize_clients
from ai_story_writer.types import (
    GenerationCompletedEvent,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
    Message,
)


def _print_messages(messages: list[Message]):
    if len(messages) == 1:
        print(messages[0].content)
    else:
        print('\n\n'.join(f'[{message.role.value}]\n{message.content}' for message in messages))


def _dry_run(messages: list[Message], model: LlmModel | None):
    _print_messages(messages)
    if model is None:
        return

    try:
        initialize_clients()
        input_tokens = count_input_tokens(messages, model)
        if input_tokens is not None:
            print(f'Input tokens: {input_tokens}')
    finally:
        cleanup_clients()


def run_generation(
    messages: list[Message],
    model: LlmModel | None,
    apply_completion: Callable[[GenerationCompletedEvent], None],
    *,
    dry_run: bool = False,
):
    if dry_run:
        _dry_run(messages, model)
        return
    if model is None:
        raise GenerationConfigError('No model configured')

    try:
        initialize_clients()
        for event in generate(messages, model):
            if isinstance(event, GenerationInProgressEvent):
                print(event.chunk, end='', flush=True)
            elif isinstance(event, GenerationCompletedEvent):
                apply_completion(event)
            elif isinstance(event, GenerationErrorEvent):
                print(f'Encountered error {event.message}', file=sys.stderr)
    finally:
        cleanup_clients()
