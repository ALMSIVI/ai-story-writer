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
