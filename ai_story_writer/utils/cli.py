from pydantic import BaseModel
from ai_story_writer.types import Story, Chapter, LlmModel


class CliChapter(BaseModel):
    id: str | None = None
    lore: str | None = None
    outline: str
    content: str | None = None

    def to_chapter(self) -> Chapter:
        if self.id is None:
            raise ValueError('id is None for chapter')
        if self.content is None:
            raise ValueError(f'content is None for chapter {self.id}')
        return Chapter(id=self.id, outline=self.outline, content=self.content, lore=self.lore)


class CliStory(BaseModel):
    id: str | None = None
    title: str
    chapters: list[CliChapter]

    def to_story_chapters(self, model: LlmModel, template: str) -> tuple[Story, list[Chapter]]:
        if self.id is None:
            raise ValueError('id is None for story')
        story = Story(id=self.id, title=self.title, model=model, template=template)
        chapters = [chapter.to_chapter() for chapter in self.chapters]
        return story, chapters


def __parse_md(md_str: str) -> list[str]:
    sections = []
    current_section = []

    for line in md_str.splitlines():
        if line.startswith('#'):
            if current_section:
                sections.append('\n'.join(current_section).strip())
                current_section = []
        current_section.append(line)

    if current_section:
        sections.append('\n'.join(current_section).strip())

    return sections


def parse_files(txt_str: str, md_str: str) -> CliStory:
    contents = __parse_md(md_str)

    txt_parts = txt_str.split('\n\n---\n\n')

    story_info = txt_parts[0].split('\n\n')
    if len(story_info) == 1:
        story_id = None
        title = story_info[0]
    else:
        story_id = story_info[0]
        title = story_info[1]

    chapters: list[CliChapter] = []
    txt_parts = txt_parts[1:]
    for i in range(0, len(txt_parts)):
        chapter_info = txt_parts[i].split('\n\n')
        if len(chapter_info) == 3:
            chapter_id = chapter_info[0]
            lore = chapter_info[1]
            outline = chapter_info[2]
        elif len(chapter_info) == 2:
            chapter_id = None
            lore = chapter_info[0]
            outline = chapter_info[1]
        else:
            chapter_id = None
            lore = None
            outline = chapter_info[0]

        content = contents[i] if i < len(contents) else None
        chapters.append(CliChapter(id=chapter_id, lore=lore, outline=outline, content=content))

    return CliStory(id=story_id, title=title, chapters=chapters)


def dump_story(cli_story: CliStory) -> tuple[str, str]:
    txt_parts = [cli_story.id, cli_story.title, '---']
    md_parts = []
    for chapter in cli_story.chapters:
        if chapter.id is not None:
            txt_parts.append(chapter.id)
        if chapter.lore is not None:
            txt_parts.append(chapter.lore)
        if chapter.outline is not None:
            txt_parts.append(chapter.outline)
        txt_parts.append('---')

        if chapter.content is not None:
            md_parts.append(chapter.content)

    txt_str = '\n\n'.join(txt_parts)
    md_str = '\n\n'.join(md_parts)
    return txt_str, md_str
