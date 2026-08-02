import sys
from collections.abc import Callable

from ai_story_writer.lib.config import GenerationConfigError
from ai_story_writer.lib.llm import cleanup_clients, count_input_tokens, generate, initialize_clients
from ai_story_writer.types import (
    GenerationCompletedEvent,
    GenerationErrorEvent,
    GenerationInProgressEvent,
    LlmModel,
)

def _dry_run(prompt: str, model: LlmModel | None):
    print(prompt)
    if model is None:
        return

    try:
        initialize_clients()
        input_tokens = count_input_tokens(prompt, model)
        if input_tokens is not None:
            print(f'Input tokens: {input_tokens}')
    finally:
        cleanup_clients()


def run_generation(
    prompt: str,
    model: LlmModel | None,
    apply_completion: Callable[[GenerationCompletedEvent], None],
    *,
    dry_run: bool = False,
):
    if dry_run:
        _dry_run(prompt, model)
        return
    if model is None:
        raise GenerationConfigError('No model configured')

    try:
        initialize_clients()
        for event in generate(prompt, model):
            if isinstance(event, GenerationInProgressEvent):
                print(event.chunk, end='', flush=True)
            elif isinstance(event, GenerationCompletedEvent):
                apply_completion(event)
            elif isinstance(event, GenerationErrorEvent):
                print(f'Encountered error {event.message}', file=sys.stderr)
    finally:
        cleanup_clients()
