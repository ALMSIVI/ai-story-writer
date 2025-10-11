from fastapi import APIRouter, HTTPException
from ai_story_writer.lib.chapter import add_chapter, delete_chapter, get_chapters, update_chapter
from ai_story_writer.types import AddChapterRequest, UpdateChapterRequest


router = APIRouter(prefix='/api/chapters')


@router.get('/{story_id}')
def get(story_id: str):
    try:
        return get_chapters(story_id)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.post('/{story_id}')
def add(story_id: str, request: AddChapterRequest):
    try:
        return add_chapter(story_id, request)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.post('/{story_id}/{chapter_id}')
def update(story_id: str, chapter_id: str, request: UpdateChapterRequest):
    try:
        return update_chapter(story_id, chapter_id, request)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.delete('/{story_id}/{chapter_id}')
def delete(story_id: str, chapter_id: str):
    try:
        return delete_chapter(story_id, chapter_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
