from ai_story_writer.types import Story


def parse_markdown(md_str: str) -> list[str]:
    sections: list[str] = []
    current_section: list[str] = []

    for line in md_str.splitlines():
        if line.startswith('# '):
            if current_section:
                sections.append('\n'.join(current_section).strip())
                current_section = []
        current_section.append(line)

    if current_section:
        sections.append('\n'.join(current_section).strip())

    return sections


def dump_markdown(story: Story) -> str:
    return '\n\n'.join(chapter.full_content for chapter in story.chapters if chapter.content is not None)
