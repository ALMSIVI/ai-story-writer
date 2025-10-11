from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import TypeAdapter
from ai_story_writer.lib.story import (
    get_stories,
    create_story,
    update_story,
    clone_story,
    delete_story,
    import_stories_from_webui,
)
from ai_story_writer.types import Story, CreateStoryRequest, WebUiChat

chat_list_validator = TypeAdapter(list[WebUiChat])
router = APIRouter(prefix='/api/stories')


@router.get('/')
def get():
    return get_stories()


@router.post('/')
def create(story: CreateStoryRequest):
    return create_story(story)


@router.put('/{story_id}')
def update(story_id: str, story: Story):
    return update_story(story_id, story)


@router.post('/{story_id}/clone')
def clone(story_id: str):
    try:
        return clone_story(story_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete('/{story_id}')
def delete(story_id: str):
    try:
        return delete_story(story_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post('/import')
def import_from_webui(file: UploadFile):
    with file.file as f:
        chats = chat_list_validator.validate_json(f.read())
        return import_stories_from_webui(chats)
