import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from jinja2 import DictLoader, Environment

from ai_story_writer.clients.__llm_client__ import LlmClient
from ai_story_writer.lib import llm, prompt
from ai_story_writer.types import Message, LlmModel


class MockClient(LlmClient):
    def __init__(self, chunks: list[str] | None = None, error: Exception | None = None):
        self.supported_models = {'model'}
        self.chunks = chunks or []
        self.error = error
        self.calls: list[tuple[list[Message], str]] = []
        self.closed = False

    def list_models(self) -> list[LlmModel]:
        return [LlmModel(provider='test', name='model')]

    def generate(self, messages: list[Message], model: str) -> Iterator[str]:
        self.calls.append((messages, model))
        if self.error is not None:
            raise self.error
        yield from self.chunks

    def close(self):
        self.closed = True

    def count_input_tokens(self, messages: list[Message], model: str) -> int | None:
        return 42


@pytest.fixture(autouse=True)
def isolate_clients():
    llm.clients.clear()
    yield
    llm.clients.clear()


@pytest.fixture
def template_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Environment:
    prompts_path = tmp_path / 'prompts'
    prompts_path.mkdir()
    (prompts_path / 'prompt.json').write_text(json.dumps({'sections': [{'name': 'prompt'}]}))
    (prompts_path / 'convo.json').write_text(json.dumps({'sections': [{'name': 'convo'}]}))
    environment = Environment(
        loader=DictLoader(
            {
                'prompt.jinja': (
                    'title={{ title }}|style={{ style }}|lore={{ lore }}|summary={{ summary }}|'
                    'previous={{ previous }}|current={{ current }}|next={{ next }}'
                ),
                'convo.jinja': 'title={{ title }}|style={{ style }}|lore={{ lore }}',
            }
        )
    )
    monkeypatch.setattr(prompt, 'prompts_path', prompts_path)
    monkeypatch.setattr(prompt, 'jinja_env', environment)
    return environment
