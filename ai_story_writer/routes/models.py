from fastapi import APIRouter

from ai_story_writer.lib.llm import get_llm_models, stop_generation


router = APIRouter(prefix='/api/models')


@router.get('/')
def get():
    return get_llm_models()


@router.post('/{generation_id}/stop')
def stop(generation_id: str):
    return stop_generation(generation_id)
