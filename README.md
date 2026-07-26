# AI Story Writer

## CLI

Story instructions are stored in YAML, while generated prose is stored in a sibling Markdown file:

```yaml
title: The Long Road
style: |-
  Lyrical prose with restrained dialogue.
chapter_count: 2

chapters:
  - lore: |-
      Rain has not stopped for a decade.
    outline: |-
      Mara reaches the western gate.

  - outline: |-
      The guard recognizes Mara.
```

Generate a chapter:

```sh
cli generate story.yaml --model OpenAI.gpt-5
```

Print the complete rendered prompt without initializing or contacting an LLM provider:

```sh
cli generate story.yaml --dry-run
```

Provide a model to also request and print the provider's input token count:

```sh
cli generate story.yaml --model OpenAI.gpt-5 --dry-run
```

`--dry-run` respects `--template`, `--id`, and `--convo`. In conversation mode,
each message is printed with its role (`system`, `user`, or `assistant`). It does
not generate prose or update the story files. Ollama does not provide an input
token-counting API, so its dry runs only print the prompt.
