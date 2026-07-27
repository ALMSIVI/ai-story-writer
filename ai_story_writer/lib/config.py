from pathlib import Path

from pydantic import ValidationError

from ai_story_writer.types import GenerationConfig


class GenerationConfigError(ValueError):
    pass


def _load_config(path: Path, *, required: bool) -> GenerationConfig | None:
    try:
        config_json = path.read_text()
    except FileNotFoundError:
        if required:
            raise GenerationConfigError(f'Configuration file does not exist: {path}')
        return None
    except OSError as error:
        raise GenerationConfigError(f'Failed to read configuration file {path}: {error}') from error

    try:
        return GenerationConfig.model_validate_json(config_json)
    except ValidationError as error:
        raise GenerationConfigError(f'Invalid configuration in {path}: {error}') from error


def resolve_generation_config(
    story_file: Path,
    story_config: GenerationConfig | None = None,
    config_file: str | None = None,
) -> GenerationConfig:
    config = GenerationConfig()
    sources = [
        _load_config(Path('config', 'config.json'), required=False),
        _load_config(story_file.parent / 'config.json', required=False),
        story_config,
    ]
    if config_file is not None:
        sources.append(_load_config(Path(config_file), required=True))

    for source in sources:
        if source is not None:
            config = config.model_copy(update=source.model_dump(exclude_none=True))

    if config.include_full_conversation is None:
        config.include_full_conversation = False
    return config
