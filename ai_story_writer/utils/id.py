from uuid import uuid4
from ai_story_writer.types import Chapter, Story


def generate_id(items: list[Story | Chapter]) -> str:
    while True:
        id = str(uuid4())
        if all(item.id != id for item in items):
            break
    return id
