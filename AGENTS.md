# AGENTS.md

## Project overview

AI Story Writer is a Python CLI that expands chapter outlines into fully-fledged stories with an LLM. The installed command is `cli`; the only current subcommand is `generate`.

The application keeps story planning data in a YAML file and generated prose in a sibling Markdown file. Generation options use layered JSON/story configuration. Provider configuration and active prompt templates live under `config/` at runtime, but only safe defaults under `config/defaults/` are tracked.

## Repository map

- `ai_story_writer/cli.py`: root parser construction, command registration, dispatch, and user-facing error handling.
- `ai_story_writer/commands/`: CLI commands; each module owns its arguments and execution workflow.
  - `ai_story_writer/commands/generate.py`: chapter selection, dry-run output, provider lifecycle, streaming, and persistence orchestration for the `generate` subcommand.
- `ai_story_writer/setup.py`: loads model configuration and registers provider clients.
- `ai_story_writer/lib/config.py`: loads and merges generation options from the supported configuration sources.
- `ai_story_writer/lib/llm.py`: prompt/conversation construction, client registry, and streaming generation events.
- `ai_story_writer/lib/yaml.py`: parser/serializer and paired YAML/Markdown file I/O for stories.
- `ai_story_writer/lib/markdown.py`: story Markdown encoding.
- `ai_story_writer/lib/id.py`: collision-safe ID generation.
- `ai_story_writer/clients/`: OpenAI, Anthropic, Google, and Ollama adapters implementing `LlmClient`.
- `ai_story_writer/types/`: Pydantic models for stories, chapters, messages, configuration, models, and generation events.
- `config/defaults/`: tracked example generation/model configuration and Jinja templates.
- `config/config.json`, `config/models.json`, and `config/templates/`: ignored local runtime configuration; never commit credentials from these paths.
- `tests/`: main test directory.
- `tests/conftest.py`: shared mock LLM client plus fixtures that isolate the global client registry and Jinja environment.

## Setup and commands

Use `uv` and the committed lockfile:

```sh
uv sync --dev
```

In sandboxed agent runs, `uv` may fail to access its default cache under `~/.cache/uv`. Use a project-specific temporary cache for all `uv` commands:

```sh
mkdir -p /tmp/ai-story-writer-uv-cache
UV_CACHE_DIR=/tmp/ai-story-writer-uv-cache uv sync --dev
UV_CACHE_DIR=/tmp/ai-story-writer-uv-cache uv run pytest -v
```

If local runtime configuration does not exist, create it from the tracked defaults, then replace placeholder credentials only in the ignored copy:

```sh
cp config/defaults/config.json config/config.json
cp config/defaults/models.json config/models.json
mkdir -p config/templates
cp config/defaults/templates/*.jinja config/templates/
```

Run the CLI from the repository root because model and template paths are relative to the current working directory:

```sh
uv run cli --help
uv run cli generate path/to/story.yaml --dry-run
uv run cli generate path/to/story.yaml
uv run cli generate path/to/story.yaml --config path/to/config.json
```

Use these checks before handing off a change:

```sh
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

## Testing

- Pytest is used as the test framework, and test discovery is configured for `tests/` in `pyproject.toml`.
- Run the complete suite with `uv run pytest -v`. During focused development, run a module or test node such as
  `uv run pytest tests/commands/test_generate.py -v` or
  `uv run pytest tests/commands/test_generate.py::test_generate_dry_run -v`.
- Keep tests deterministic and network-free. Use `tmp_path` for story/config files, `mocker.patch` for SDK and lifecycle boundaries, `monkeypatch` for process state such as the working directory, and `capsys` for CLI output.
- Patch generation dependencies on `ai_story_writer.commands.generate` in command tests. Keep `tests/test_cli.py` focused on parser registration, dispatch, compatibility exports, and conversion of known failures to parser errors.
- The fixture in `tests/conftest.py` clears `ai_story_writer.lib.llm.clients` before and after every test. Register mock clients explicitly when exercising generation.
- Provider adapter tests live in separate modules under `tests/clients/`. Patch each adapter's SDK constructor to return a mock, then assert translated roles, system-message handling, stream shapes, model filtering, errors, and close behavior without constructing live SDK clients.
- Prompt tests should use an isolated Jinja environment rather than reading ignored runtime templates. File and CLI tests must not modify repository data or configuration.

## Core behavior and data contracts

- Models are selected as `<provider>.<model>` and parsed by splitting on the first period. Provider names are case-sensitive and must match keys in `config/models.json` and the client registry.
- All user-facing configuration keys in JSON and YAML must be camelCase, while Python fields and other internal names must be snake_case. Define Pydantic aliases for this boundary; for example, `includeFullConversation` maps to `include_full_conversation` and `apiKey` maps to `api_key`.
- `GenerationConfig` contains `model`, `template`, `includeFullConversation`, and `fullChapterCount`. Story YAML reuses this model as the optional nested `config` field. `Story` contains only story-domain data; `YamlStoryDocument` exposes the parsed `Story` and `GenerationConfig` separately.
- Generation options are merged one field at a time in descending priority: the file passed with `-c/--config`, the story's nested `config`, `config.json` beside the story YAML, then the project's `config/config.json`. Missing implicit files are skipped; a missing explicit file is an error.
- Non-conversation generation renders one user prompt from `config/templates/<name>.jinja`. `includeFullConversation: true` instead emits a system message followed by alternating outline/user and chapter/assistant messages.
- In standard prompt mode, `fullChapterCount` controls how many recent previous chapters are included as full prose. Older chapters use their outlines as summaries; `0` summarizes all previous chapters, while `null` includes all previous chapters in full.
- Generation is streamed as `GenerationInProgressEvent` objects, followed by either one completion or one error event. Keep provider-specific SDK objects inside the adapters; the rest of the application should use the shared `Message`, `Role`, and event models.
- A generated chapter title is recognized only when the content starts with `# `. `Chapter` stores that title separately and reconstructs it through `full_content` and `full_outline`.
- Chapter lore inherits from the nearest preceding chapter when the current chapter has no lore.

## Story file format

The input `.yaml` document contains a story and an optional nested generation configuration. Generation options live separately under the top-level `config` key and must not be added to `Story`. Use YAML literal blocks for human-editable multiline text.

Generated content is written to a sibling `.md` file. Top-level `# ` headings delimit chapters, so changes to heading handling or blank-line separators can break round trips. When modifying parsing or serialization, add round-trip tests covering omitted optional fields, titled and untitled content, lore inheritance, multiple chapters, and preservation of YAML comments and multiline scalar styles.

## Change guidelines

- Follow the configured Ruff style: 120-character lines and single quotes.
- Keep public imports centralized in `ai_story_writer/types/__init__.py` and `ai_story_writer/clients/__init__.py` when adding shared types or clients.
- Add future CLI functions as self-registering modules under `ai_story_writer/commands/`. Command modules should own their arguments and orchestration; keep `ai_story_writer/cli.py` limited to root-parser concerns.
- Put application-specific configuration, persistence, identifier, prompt, and generation helpers under `ai_story_writer/lib/`; do not recreate a generic `utils` package.
- Add type hints and Pydantic validation at external/configuration boundaries. Preserve iterator-based streaming rather than buffering provider output in adapters.
- Keep dry runs file-write-free: they render and print messages without generating prose or rewriting story files. When the resolved configuration contains a model, dry runs initialize that provider and may contact it to count input tokens; without a model they must remain provider-free.
- Do not make live provider calls in automated tests. Mock the shared client interface or inject a mock client into `ai_story_writer.lib.llm.clients`.
- Test provider adapters separately from prompt/file logic. Provider APIs differ in system-message handling, roles, stream event shapes, and close semantics.
- When touching CLI lifecycle code, verify both dry-run and real-generation paths, including client initialization and cleanup on exceptions.
- Preserve user-owned ignored files under `data/`, `config/config.json`, `config/models.json`, and `config/templates/`. Never print, copy into tracked files, or commit local API keys.
- Keep edits focused. The repository may contain unrelated local changes; inspect `git status` before and after work and do not overwrite them.
