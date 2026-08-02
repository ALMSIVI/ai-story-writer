from ai_story_writer.lib.prompt import render_prompt
from ai_story_writer.types import Message, Role, Story


def _validate_chapter_index(story: Story, chapter_index: int):
    if chapter_index < 0 or chapter_index >= len(story.chapters):
        raise IndexError(f'chapter index {chapter_index} out of range')


def _get_lore(story: Story, chapter_index: int) -> str | None:
    for chapter in reversed(story.chapters[: chapter_index + 1]):
        if chapter.lore is not None:
            return chapter.lore
    return None


def _create_prompt(
    story: Story,
    chapter_index: int,
    template: str,
    full_chapter_count: int | None,
) -> str:
    previous_chapters = story.chapters[:chapter_index]
    current_chapter = story.chapters[chapter_index]

    if full_chapter_count is not None and len(previous_chapters) > full_chapter_count:
        summary_length = len(previous_chapters) - full_chapter_count
        summary = '\n\n'.join(chapter.full_outline for chapter in previous_chapters[:summary_length])
        previous_contents = '\n\n'.join(chapter.full_content for chapter in previous_chapters[summary_length:])
    else:
        summary = None
        previous_contents = '\n\n'.join(chapter.full_content for chapter in previous_chapters)

    next_outline = ''
    if chapter_index < len(story.chapters) - 1:
        next_outline = story.chapters[chapter_index + 1].outline

    return render_prompt(
        template,
        {
            'title': story.title,
            'style': story.style,
            'lore': _get_lore(story, chapter_index),
            'summary': summary,
            'previous': previous_contents,
            'current': current_chapter.outline,
            'next': next_outline,
        },
    )


def _create_history(
    story: Story,
    chapter_index: int,
    template: str,
) -> list[Message]:
    system_message = render_prompt(
        template,
        {
            'title': story.title,
            'style': story.style,
            'lore': _get_lore(story, chapter_index),
        },
    )

    messages = [Message(role=Role.SYSTEM, content=system_message)]

    for chapter in story.chapters[:chapter_index]:
        messages.append(Message(role=Role.USER, content=chapter.outline))
        messages.append(Message(role=Role.ASSISTANT, content=chapter.full_content))

    messages.append(Message(role=Role.USER, content=story.chapters[chapter_index].outline))
    return messages


def create_messages(
    story: Story,
    chapter_index: int,
    template: str,
    include_full_conversation: bool = False,
    full_chapter_count: int | None = None,
) -> list[Message]:
    """Build the complete LLM input without contacting a provider."""
    _validate_chapter_index(story, chapter_index)

    if include_full_conversation:
        return _create_history(story, chapter_index, template)

    prompt = _create_prompt(story, chapter_index, template, full_chapter_count)
    return [Message(role=Role.USER, content=prompt)]
