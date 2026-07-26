from collections.abc import Iterator

import pytest
from jinja2 import DictLoader, Environment

from ai_story_writer.clients.__llm_client__ import LlmClient
from ai_story_writer.lib import llm
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

    def close(self) -> None:
        self.closed = True

    def count_input_tokens(self, messages: list[Message], model: str) -> int | None:
        return 42


@pytest.fixture(autouse=True)
def isolate_clients():
    llm.clients.clear()
    yield
    llm.clients.clear()


@pytest.fixture
def template_environment(monkeypatch: pytest.MonkeyPatch) -> Environment:
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
    monkeypatch.setattr(llm, 'jinja_env', environment)
    return environment
