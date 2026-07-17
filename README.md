# AI Story Writer

## CLI

Generate a chapter:

```sh
cli generate --file story.txt --model OpenAI.gpt-5
```

Print the complete rendered prompt without initializing or contacting an LLM provider:

```sh
cli generate --file story.txt --dry-run
```

`--dry-run` respects `--template`, `--id`, and `--convo`. In conversation mode,
each message is printed with its role (`system`, `user`, or `assistant`). It does
not update the story files.
