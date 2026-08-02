from pathlib import Path
from typing import Iterator
from pydantic import TypeAdapter

from ai_story_writer.clients import LlmClient, AnthropicClient, GoogleClient, OpenAIClient, OllamaClient
from ai_story_writer.types import (
    GenerationCompletedEvent,
    GenerationErrorEvent,
    ModelConfig,
    GenerationEvent,
    GenerationInProgressEvent,
    LlmModel,
)

clients: dict[str, LlmClient] = {}


def _add_client(provider: str, model_config: ModelConfig):
    supported_models = set(model_config.supported_models if model_config.supported_models is not None else [])
    match provider:
        case 'Anthropic':
            clients[provider] = AnthropicClient(
                api_key=model_config.api_key,
                supported_models=supported_models,
            )
        case 'Google':
            clients[provider] = GoogleClient(
                api_key=model_config.api_key,
                supported_models=supported_models,
            )
        case 'Ollama':
            clients[provider] = OllamaClient(
                api_key=model_config.api_key,
                supported_models=supported_models,
                provider=provider,
                base_url=model_config.base_url,
            )
        case _:
            sdk = model_config.base_sdk
            match sdk:
                case 'Anthropic':
                    clients[provider] = AnthropicClient(
                        api_key=model_config.api_key,
                        supported_models=supported_models,
                        provider=provider,
                        base_url=model_config.base_url,
                    )
                case _:
                    clients[provider] = OpenAIClient(
                        api_key=model_config.api_key,
                        supported_models=supported_models,
                        provider=provider,
                        base_url=model_config.base_url,
                    )


models_config_adapter = TypeAdapter(dict[str, ModelConfig])


def initialize_clients():
    models = Path('config', 'models.json')
    with models.open() as f:
        models_config = models_config_adapter.validate_json(f.read())
        for provider, model_config in models_config.items():
            _add_client(provider, model_config)


def cleanup_clients():
    for client in clients.values():
        client.close()
    clients.clear()


def _get_client(model: LlmModel) -> LlmClient:
    if model.provider not in clients:
        raise ValueError(f'client {model.provider} does not exist')

    client = clients[model.provider]
    if model.name not in client.supported_models:
        raise ValueError(f'model {model.name} not supported in client {model.provider}')
    return client


def count_input_tokens(prompt: str, model: LlmModel) -> int | None:
    client = _get_client(model)
    return client.count_input_tokens(prompt, model.name)


def generate(prompt: str, model: LlmModel) -> Iterator[GenerationEvent]:
    client = _get_client(model)
    try:
        generation = client.generate(prompt, model.name)
        content = ''
        for chunk in generation:
            content += chunk
            yield GenerationInProgressEvent(chunk=chunk)

        yield GenerationCompletedEvent(content=content)
    except Exception as e:
        yield GenerationErrorEvent(message=str(e))
