from pathlib import Path
from pydantic import TypeAdapter
from ai_story_writer.types import Story

story_list_adapter = TypeAdapter(list[Story])
story_path = Path('data', 'stories.json')


def read_stories() -> list[Story]:
    with story_path.open() as f:
        return story_list_adapter.validate_json(f.read())


def write_stories(stories: list[Story] | None = None):
    with story_path.open('wt') as f:
        f.write(story_list_adapter.dump_json(stories))
