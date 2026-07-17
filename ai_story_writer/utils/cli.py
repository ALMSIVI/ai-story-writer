from uuid import UUID
from ai_story_writer.types import Story, Chapter

def __parse_md(md_str: str) -> list[str]:
    sections = []
    current_section = []

    for line in md_str.splitlines():
        if line.startswith('# '):
            if current_section:
                sections.append('\n'.join(current_section).strip())
                current_section = []
        current_section.append(line)

    if current_section:
        sections.append('\n'.join(current_section).strip())

    return sections


def parse_files(txt_str: str, md_str: str) -> Story:
    contents = __parse_md(md_str)
    txt_parts = txt_str.split('\n\n---\n\n')
    story_info = txt_parts[0].split('\n\n')

    # Title is required, all others are optional
    # Order is: id, title, style, chapter_count
    if len(story_info) == 4:
        story_id = story_info[0]
        title = story_info[1]
        style = story_info[2]
        chapter_count = int(story_info[3])
    elif len(story_info) == 3:
        try:
            UUID(story_info[0])
            story_id = story_info[0]
        except ValueError:
            story_id = None

        if story_id is not None:
            title = story_info[1]
            try:
                style = None
                chapter_count = int(story_info[2])
            except ValueError:
                style = story_info[2]
                chapter_count = None
        else:
            title = story_info[0]
            style = story_info[1]
            chapter_count = int(story_info[2])
    elif len(story_info) == 2:
        try:
            UUID(story_info[0])
            story_id = story_info[0]
        except ValueError:
            story_id = None

        if story_id is not None:
            title = story_info[1]
            style = None
            chapter_count = None
        else:
            title = story_info[0]
            try:
                style = None
                chapter_count = int(story_info[1])
            except ValueError:
                style = story_info[1]
                chapter_count = None
    else:
        story_id = None
        title = story_info[0]
        style = None
        chapter_count = None

    chapters: list[Chapter] = []
    txt_parts = txt_parts[1:]
    for i in range(0, len(txt_parts)):
        chapter_info = txt_parts[i].split('\n\n')
        if len(chapter_info) == 3:
            chapter_id = chapter_info[0]
            lore = chapter_info[1]
            outline = chapter_info[2]
        elif len(chapter_info) == 2:
            try:
                UUID(chapter_info[0])
                chapter_id = chapter_info[0]
                lore = None
                outline = chapter_info[1]
            except ValueError:
                chapter_id = None
                lore = chapter_info[0]
                outline = chapter_info[1]
        else:
            chapter_id = None
            lore = None
            outline = chapter_info[0]

        content = contents[i] if i < len(contents) else None
        chapters.append(Chapter(id=chapter_id, lore=lore, outline=outline, content=content))

    return Story(id=story_id, title=title, style=style, chapter_count=chapter_count, chapters=chapters)


def dump_story(story: Story) -> tuple[str, str]:
    txt_parts: list[str] = []
    if story.id is not None:
        txt_parts.append(story.id)
    txt_parts.append(story.title)
    if story.style is not None:
        txt_parts.append(story.style)
    if story.chapter_count is not None:
        txt_parts.append(str(story.chapter_count))
    txt_parts.append('---')

    md_parts: list[str] = []
    for chapter in story.chapters:
        if chapter.id is not None:
            txt_parts.append(chapter.id)
        if chapter.lore is not None:
            txt_parts.append(chapter.lore)

        txt_parts.append(chapter.outline)
        txt_parts.append('---')

        if chapter.content is not None:
            md_parts.append(chapter.full_content)

    # Remove final ---
    txt_parts = txt_parts[:-1]

    txt_str = '\n\n'.join(txt_parts)
    md_str = '\n\n'.join(md_parts)
    return txt_str, md_str
