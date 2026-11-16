from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scalarstring import LiteralScalarString

from ai_story_writer.lib.markdown import dump_markdown, parse_markdown
from ai_story_writer.types import Background, Chapter, Character, GenerationConfig, Story


class StoryFileError(ValueError):
    pass


class ChapterInstructions(BaseModel):
    model_config = ConfigDict(extra='forbid')

    id: str | None = None
    background: list[Background] | None = None
    outline: str


class StoryFileInstructions(BaseModel):
    model_config = ConfigDict(extra='forbid')

    id: str | None = None
    title: str
    style: str | None = None
    background: list[Background] | None = None
    characters: list[Character] | None = None
    config: GenerationConfig | None = None
    chapters: list[ChapterInstructions]


def _yaml() -> YAML:
    yaml = YAML(typ='rt')
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    return yaml


def _literal(value: str) -> LiteralScalarString:
    return LiteralScalarString(value)


def _background_entries(entries: list[Background]) -> CommentedSeq:
    return CommentedSeq(
        _literal(entry.content)
        if entry.keywords is None
        else CommentedMap(keywords=CommentedSeq(entry.keywords), content=_literal(entry.content))
        for entry in entries
    )


@dataclass
class YamlStoryDocument:
    story: Story
    generation_config: GenerationConfig | None
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
            instructions = StoryFileInstructions.model_validate(document)
        except ValidationError as error:
            raise StoryFileError(f'Invalid story instructions: {error}') from error

        contents = parse_markdown(md_str)
        chapters = [
            Chapter(
                id=chapter.id,
                background=chapter.background,
                outline=chapter.outline,
                content=contents[index] if index < len(contents) else None,
            )
            for index, chapter in enumerate(instructions.chapters)
        ]
        story = Story(
            id=instructions.id,
            title=instructions.title,
            style=instructions.style,
            background=instructions.background,
            characters=instructions.characters,
            chapters=chapters,
        )
        return cls(story=story, generation_config=instructions.config, document=document)

    @classmethod
    def load_files(cls, yaml_path: Path) -> 'YamlStoryDocument':
        yaml_str = yaml_path.read_text()
        markdown_path = yaml_path.with_suffix('.md')
        md_str = markdown_path.read_text() if markdown_path.exists() else ''
        return cls.load(yaml_str, md_str)

    @classmethod
    def from_story(
        cls,
        story: Story,
        generation_config: GenerationConfig | None = None,
    ) -> 'YamlStoryDocument':
        document = CommentedMap()
        if story.id is not None:
            document['id'] = story.id
        document['title'] = story.title
        if story.style is not None:
            document['style'] = _literal(story.style)
        if story.background is not None:
            document['background'] = _background_entries(story.background)
        if story.characters is not None:
            characters = CommentedSeq()
            for character in story.characters:
                entry = CommentedMap(name=character.name)
                if character.keywords is not None:
                    entry['keywords'] = CommentedSeq(character.keywords)
                entry['content'] = _literal(character.content)
                characters.append(entry)
            document['characters'] = characters
        if generation_config is not None:
            document['config'] = CommentedMap(generation_config.model_dump(by_alias=True, exclude_none=True))

        chapters = CommentedSeq()
        for chapter in story.chapters:
            chapter_document = CommentedMap()
            if chapter.id is not None:
                chapter_document['id'] = chapter.id
            if chapter.background is not None:
                chapter_document['background'] = _background_entries(chapter.background)
            chapter_document['outline'] = _literal(chapter.outline)
            chapters.append(chapter_document)
        document['chapters'] = chapters
        return cls(story=story, generation_config=generation_config, document=document)

    def set_story_id(self, story_id: str):
        self.story.id = story_id
        if 'id' in self.document:
            self.document['id'] = story_id
        else:
            self.document.insert(0, 'id', story_id)

    def set_chapter_id(self, index: int, chapter_id: str):
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

    def write_files(self, yaml_path: Path):
        yaml_path.write_text(self.dump())
        yaml_path.with_suffix('.md').write_text(dump_markdown(self.story))

    def _chapter_document(self, index: int) -> CommentedMap:
        chapters = self.document['chapters']
        chapter = chapters[index]
        if not isinstance(chapter, CommentedMap):
            raise StoryFileError(f'Chapter {index + 1} must be a mapping')
        return chapter
