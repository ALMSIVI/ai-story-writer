# AI Story Writer

## CLI

Story instructions are stored in YAML, while generated prose is stored in a sibling Markdown file:

```yaml
title: The Long Road
style: |-
  Lyrical prose with restrained dialogue.
config:
  model: OpenAI.gpt-5
  template: write
  includeFullConversation: false
  fullChapterCount: 2

chapters:
  - lore: |-
      Rain has not stopped for a decade.
    outline: |-
      Mara reaches the western gate.

  - outline: |-
      The guard recognizes Mara.
```

Write a chapter:

```sh
cli write story.yaml
```

Generation options can be set in JSON:

```json
{
    "model": "OpenAI.gpt-5",
    "template": "write",
    "includeFullConversation": false,
    "fullChapterCount": null
}
```

Copy the defaults to create the active project configuration:

```sh
cp config/defaults/config.json config/config.json
mkdir -p config/prompts config/templates
cp config/defaults/prompts/*.json config/prompts/
cp config/defaults/templates/*.jinja config/templates/
```

Options are merged one field at a time, from highest to lowest priority:

1. A file passed with `-c/--config`
2. The nested `config` options in the story YAML
3. `config.json` in the story YAML's directory
4. The project's `config/config.json`

For example, use a particular configuration file with:

```sh
cli write story.yaml --config configs/draft.json
```

Print the complete rendered prompt with:

```sh
cli write story.yaml --dry-run
```

When the resolved configuration includes a model, a dry run initializes that provider and requests an input token count. Without a model, it only prints the prompt. In conversation mode, each message is printed with its role (`system`, `user`, or `assistant`). Dry runs do not generate prose or update story files. Ollama does not provide an input token-counting API, so its dry runs only print the prompt.

`includeFullConversation` switches to chatbot-style history: every previous outline is sent as a user message and every generated chapter as an assistant message. `fullChapterCount` controls how many of the most recent previous chapters are included as full prose in the standard prompt; older chapters are represented by their outlines to save tokens. Set it to `0` to summarize every previous chapter by outline, or `null` to include all previous chapters in full.

## Prompt templates

The configured `template` name resolves to a JSON composition in `config/prompts/`. For example,
`"template": "write"` loads `config/prompts/write.json`:

```json
{
    "sections": [
        {"name": "next-chapter-role"},
        {"name": "story-lore"},
        {"name": "future-context", "enabled": false}
    ]
}
```

Each enabled entry loads the matching Jinja section from `config/templates/`, such as `config/templates/story-lore.jinja`. `enabled` is optional and defaults to `true`, so sections can be temporarily disabled without removing them from the composition. Enabled sections are rendered in order with the same story and chapter context. Empty sections are omitted, and the remaining sections are joined with a blank line.
