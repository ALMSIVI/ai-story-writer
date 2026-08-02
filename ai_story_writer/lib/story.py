from uuid import uuid4

from ai_story_writer.types import Story, Chapter


def generate_id(items: list[Story] | list[Chapter]) -> str:
    while True:
        id = str(uuid4())
        if all(item.id != id for item in items):
            break
    return id


def find_chapter_index(story: Story, chapter_id: str | None) -> int:
    if chapter_id is None:
        try:
            return next(index for index, chapter in enumerate(story.chapters) if chapter.id is None)
        except StopIteration:
            raise KeyError('Cannot find chapter without id') from None

    try:
        return next(index for index, chapter in enumerate(story.chapters) if chapter.id == chapter_id)
    except StopIteration:
        raise KeyError(f'Cannot find chapter with id {chapter_id}') from None


def get_lore(story: Story, chapter_index: int) -> str | None:
    for chapter in reversed(story.chapters[: chapter_index + 1]):
        if chapter.lore is not None:
            return chapter.lore
    return None


def get_previous_context(
    story: Story,
    chapter_index: int,
    full_chapter_count: int | None,
):
    previous_chapters = story.chapters[:chapter_index]
    if full_chapter_count is not None and len(previous_chapters) > full_chapter_count:
        summary_length = len(previous_chapters) - full_chapter_count
        summary = '\n\n'.join(chapter.full_outline for chapter in previous_chapters[:summary_length])
        contents = '\n\n'.join(chapter.full_content for chapter in previous_chapters[summary_length:])
    else:
        summary = None
        contents = '\n\n'.join(chapter.full_content for chapter in previous_chapters)

    return summary, contents


def get_next_outline(story: Story, chapter_index: int):
    if chapter_index < len(story.chapters) - 1:
        return story.chapters[chapter_index + 1].outline
    return None
