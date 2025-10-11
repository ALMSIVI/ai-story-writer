from fastapi import APIRouter

from ai_story_writer.lib.llm import get_llm_models


router = APIRouter(prefix='/api/models')


@router.get('/')
def get():
    return get_llm_models()
