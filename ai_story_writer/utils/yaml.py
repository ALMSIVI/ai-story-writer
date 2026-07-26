from dataclasses import dataclass
from io import StringIO

from pydantic import BaseModel, ConfigDict, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scalarstring import LiteralScalarString

from ai_story_writer.types import Chapter, Story
from ai_story_writer.utils.markdown import parse_markdown


class StoryFileError(ValueError):
    pass


class ChapterInstructions(BaseModel):
    model_config = ConfigDict(extra='forbid')

    id: str | None = None
    lore: str | None = None
    outline: str


class StoryInstructions(BaseModel):
    model_config = ConfigDict(extra='forbid')

    id: str | None = None
    title: str
    style: str | None = None
    chapter_count: int | None = None
    chapters: list[ChapterInstructions]


def _yaml() -> YAML:
    yaml = YAML(typ='rt')
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    return yaml


def _literal(value: str) -> LiteralScalarString:
    return LiteralScalarString(value)


@dataclass
class YamlStoryDocument:
    story: Story
    document: CommentedMap

    @classmethod
    def load(cls, yaml_str: str, md_str: str = '') -> 'YamlStoryDocument':
        try:
            document = _yaml().load(yaml_str)
        except YAMLError as error:
            raise StoryFileError(f'Invalid YAML: {error}') from error

        if not isinstance(document, CommentedMap):
            raise StoryFileError('Story YAML must contain a top-level mapping')

        try:
            instructions = StoryInstructions.model_validate(document)
        except ValidationError as error:
            raise StoryFileError(f'Invalid story instructions: {error}') from error

        contents = parse_markdown(md_str)
        chapters = [
            Chapter(
                id=chapter.id,
                lore=chapter.lore,
                outline=chapter.outline,
                content=contents[index] if index < len(contents) else None,
            )
            for index, chapter in enumerate(instructions.chapters)
        ]
        story = Story(
            id=instructions.id,
            title=instructions.title,
            style=instructions.style,
            chapter_count=instructions.chapter_count,
            chapters=chapters,
        )
        return cls(story=story, document=document)

    @classmethod
    def from_story(cls, story: Story) -> 'YamlStoryDocument':
        document = CommentedMap()
        if story.id is not None:
            document['id'] = story.id
        document['title'] = story.title
        if story.style is not None:
            document['style'] = _literal(story.style)
        if story.chapter_count is not None:
            document['chapter_count'] = story.chapter_count

        chapters = CommentedSeq()
        for chapter in story.chapters:
            chapter_document = CommentedMap()
            if chapter.id is not None:
                chapter_document['id'] = chapter.id
            if chapter.lore is not None:
                chapter_document['lore'] = _literal(chapter.lore)
            chapter_document['outline'] = _literal(chapter.outline)
            chapters.append(chapter_document)
        document['chapters'] = chapters
        return cls(story=story, document=document)

    def set_story_id(self, story_id: str) -> None:
        self.story.id = story_id
        if 'id' in self.document:
            self.document['id'] = story_id
        else:
            self.document.insert(0, 'id', story_id)

    def set_chapter_id(self, index: int, chapter_id: str) -> None:
        self.story.chapters[index].id = chapter_id
        chapter = self._chapter_document(index)
        if 'id' in chapter:
            chapter['id'] = chapter_id
        else:
            chapter.insert(0, 'id', chapter_id)

    def dump(self) -> str:
        stream = StringIO()
        _yaml().dump(self.document, stream)
        return stream.getvalue()

    def _chapter_document(self, index: int) -> CommentedMap:
        chapters = self.document['chapters']
        chapter = chapters[index]
        if not isinstance(chapter, CommentedMap):
            raise StoryFileError(f'Chapter {index + 1} must be a mapping')
        return chapter
