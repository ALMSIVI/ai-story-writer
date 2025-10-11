from pathlib import Path
from pydantic import TypeAdapter
from .story import read_stories
from ai_story_writer.types import Chapter


chapter_list_adapter = TypeAdapter(list[Chapter])
chapters_path = Path('data', 'chapters')


def __check_story_existence(story_id: str):
    stories = read_stories()
    if all(story.id != story_id for story in stories):
        raise KeyError(f'Story {story_id} not found')


def read_chapters(story_id: str) -> list[Chapter]:
    __check_story_existence(story_id)
    chapter_path = chapters_path / f'{story_id}.json'
    if not chapter_path.exists():
        return []

    with chapter_path.open() as f:
        return chapter_list_adapter.validate_json(f.read())


def write_chapters(story_id: str, chapters: list[Chapter] | None = None):
    __check_story_existence(story_id)
    chapter_path = chapters_path / f'{story_id}.json'
    with chapter_path.open('wb') as f:
        if chapters is None:
            chapters = []
        f.write(chapter_list_adapter.dump_json(chapters, exclude_none=True))


def delete_chapters(story_id: str):
    chapter_path = chapters_path / f'{story_id}.json'
    chapter_path.unlink(missing_ok=True)
