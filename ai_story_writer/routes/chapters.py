from typing import Iterator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ai_story_writer.lib.chapter import add_chapter, delete_chapter, get_chapters, regenerate_chapter, update_chapter
from ai_story_writer.types import AddChapterRequest, UpdateChapterRequest, GenerationEvent


router = APIRouter(prefix='/api/chapters')


def __to_sse_event(response: Iterator[GenerationEvent]):
    for event in response:
        yield f'event: {event.event_type}\ndata: {event.model_dump_json()}'


@router.get('/{story_id}')
def get(story_id: str):
    try:
        return get_chapters(story_id)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.post('/{story_id}')
def add(story_id: str, request: AddChapterRequest):
    try:
        return StreamingResponse(__to_sse_event(add_chapter(story_id, request), media_type='text/event-stream'))
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.put('/{story_id}/{chapter_id}')
def update(story_id: str, chapter_id: str, request: UpdateChapterRequest):
    try:
        return update_chapter(story_id, chapter_id, request)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.put('/{story_id}/{chapter_id}/regenerate')
def regenerate(story_id: str, chapter_id: str):
    try:
        return StreamingResponse(
            __to_sse_event(regenerate_chapter(story_id, chapter_id)), media_type='text/event-stream'
        )
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.delete('/{story_id}/{chapter_id}')
def delete(story_id: str, chapter_id: str):
    try:
        return delete_chapter(story_id, chapter_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
