from typing import Iterator
from .story import get_story, update_story
from .llm import generate_chapter
from ai_story_writer.utils.id import generate_id
from ai_story_writer.data.chapter import read_chapters, write_chapters
from ai_story_writer.types import (
    CreateChapterRequest,
    Chapter,
    GenerationEvent,
    GenerationCompletedEvent,
)


def get_chapters(story_id: str):
    return read_chapters(story_id)


def __find_chapter(story_id: str, chapter_id: str, chapters: list[Chapter] | None = None):
    if chapters is None:
        chapters = get_chapters(story_id)
    try:
        return next(i for i, c in enumerate(chapters) if c.id == chapter_id)
    except StopIteration:
        raise KeyError(f'Chapter {chapter_id} not found')


def add_chapter(story_id: str, request: CreateChapterRequest) -> Iterator[GenerationEvent]:
    story = get_story(story_id)
    if request.model:
        story.model = request.model

    all_chapters = get_chapters(story_id)
    previous_chapters = all_chapters
    index = -1
    if request.after:
        index = __find_chapter(story_id, request.after, all_chapters)
        previous_chapters = all_chapters[: index + 1]

    next_outline = request.next_outline
    if len(previous_chapters) != len(all_chapters):
        next_outline = all_chapters[index + 2].outline

    lore = request.lore
    if lore is None:
        for chapter in reversed(previous_chapters):
            if chapter.lore is not None:
                lore = chapter.lore
                break

    for event in generate_chapter(
        story, lore, request.current_outline, previous_chapters, next_outline, story.include_full_convo
    ):
        if isinstance(event, GenerationCompletedEvent):
            completed_event: GenerationCompletedEvent = event
            current_chapter = Chapter(
                id=generate_id(all_chapters),
                outline=request.current_outline,
                content=completed_event.content,
                lore=request.lore,
                model=story.model,
            )
            if request.after:
                all_chapters = previous_chapters + [current_chapter] + all_chapters[index + 2 :]
            else:
                all_chapters.append(current_chapter)
                story.next_outline = next_outline

            write_chapters(story_id, all_chapters)
            update_story(story_id, story)

            yield GenerationCompletedEvent(interrupted=completed_event.interrupted, chapter=current_chapter)
        else:
            yield event


def update_chapter(story_id: str, chapter_id: str, chapter: Chapter):
    story = get_story(story_id)
    all_chapters = get_chapters(story_id)
    index = __find_chapter(story_id, chapter_id, all_chapters)
    chapter.id = chapter_id
    all_chapters[index] = chapter

    write_chapters(story_id, all_chapters)
    if chapter.model:
        update_story(story_id, story)

    return chapter


def regenerate_chapter(story_id: str, chapter_id: str):
    story = get_story(story_id)
    all_chapters = get_chapters(story_id)
    index = __find_chapter(story_id, chapter_id, all_chapters)
    chapter = all_chapters[index]
    previous_chapters = all_chapters[:index]

    next_outline = None
    if index < len(all_chapters) - 1:
        next_outline = all_chapters[index + 1].outline

    lore = chapter.lore
    if lore is None:
        for chapter in reversed(previous_chapters):
            if chapter.lore is not None:
                lore = chapter.lore
                break

    for event in generate_chapter(
        story, lore, chapter.outline, previous_chapters, next_outline, story.include_full_convo
    ):
        if isinstance(event, GenerationCompletedEvent):
            completed_event: GenerationCompletedEvent = event
            write_chapters(story_id, all_chapters)
            yield GenerationCompletedEvent(interrupted=completed_event.interrupted, content=chapter)
        else:
            yield event


def delete_chapter(story_id: str, chapter_id: str):
    chapters = get_chapters(story_id)
    index = __find_chapter(story_id, chapter_id, chapters)
    deleted_chapter = chapters[index]
    chapters.remove(deleted_chapter)
    write_chapters(story_id, chapters)
    return deleted_chapter
