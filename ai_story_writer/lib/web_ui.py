from ai_story_writer.types import LlmModel, WebUiChat, Story, Chapter


def convert_to_story(chat: WebUiChat) -> tuple[Story, list[Chapter]]:
    history = list(chat.chat.history.messages.values())
    messages = history if len(history) > len(chat.chat.messages) else chat.chat.messages
    story = Story(id=chat.id, title=chat.title, model=LlmModel.parse(chat.chat.models[0]))
    chapters: list[Chapter] = []
    for i in range(2, len(messages), 2):
        chapters.append(
            Chapter(
                id=messages[i].id,
                outline=messages[i].content,
                content=messages[i + 1].content,
                model=LlmModel.parse(messages[i + 1].model),
            ),
        )
    chapters[0].lore = messages[0].content
    return story, chapters
