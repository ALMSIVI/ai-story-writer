from pathlib import Path
from pydantic import TypeAdapter
from ai_story_writer.types import Chapter

chapter_list_adapter = TypeAdapter(list[Chapter])
chapters_path = Path('data', 'chapters')


def read_chapters(story_id: str) -> list[Chapter]:
    chapter_path = chapters_path / f'{story_id}.json'
    with chapter_path.open() as f:
        return chapter_list_adapter.validate_json(f.read())


def save_chapters(story_id: str, chapters: list[Chapter] | None = None):
    chapter_path = chapters_path / f'{story_id}.json'
    with chapter_path.open('w') as f:
        if chapters is None:
            f.write('[]')
        else:
            f.write(chapter_list_adapter.dump_json(chapters))


def delete_chapters(story_id: str):
    chapter_path = chapters_path / f'{story_id}.json'
    chapter_path.unlink(missing_ok=True)
