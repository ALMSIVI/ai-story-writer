from pathlib import Path
from pydantic import TypeAdapter
from ai_story_writer.lib.llm import add_client, cleanup_clients
from ai_story_writer.types import ModelConfig

models_config_adapter = TypeAdapter(dict[str, ModelConfig])


def initialize_clients():
    models = Path('config', 'models.json')
    with models.open() as f:
        models_config = models_config_adapter.validate_json(f.read())
        for provider, model_config in models_config.items():
            add_client(provider, model_config)


def setup():
    initialize_clients()


def teardown():
    cleanup_clients()
