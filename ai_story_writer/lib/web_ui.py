from ai_story_writer.types import LlmModel, WebUiChat, Story, Chapter


def parse_model(model_str: str) -> LlmModel:
    try:
        index = model_str.index('.')
    except ValueError:
        # TODO: local model support
        raise ValueError(f'Failed to parse model {model_str}')

    return LlmModel(provider=model_str[:index], name=model_str[index + 1 :])


def convert_to_story(chat: WebUiChat) -> tuple[Story, list[Chapter]]:
    history = list(chat.chat.history.messages.values())
    messages = history if len(history) > len(chat.chat.messages) else chat.chat.messages
    story = Story(id=chat.id, title=chat.title, model=parse_model(chat.chat.models[0]))
    chapters: list[Chapter] = []
    for i in range(2, len(messages), 2):
        chapters.append(
            Chapter(
                id=messages[i].id,
                outline=messages[i].content,
                content=messages[i + 1].content,
                model=parse_model(messages[i + 1].model),
            ),
        )
    chapters[0].lore = messages[0].content
    return story, chapters
