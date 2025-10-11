from ai_story_writer.data.story import read_stories, write_stories
from ai_story_writer.data.chapter import delete_chapters, write_chapters
from ai_story_writer.lib.web_ui import convert_to_story
from ai_story_writer.types import Story, WebUiChat
from ai_story_writer.utils.id import generate_id


def get_stories():
    return read_stories()


def get_story(story_id: str, stories: list[Story] = None):
    if stories is None:
        stories = get_stories()
    try:
        return next(story for story in stories if story.id == story_id)
    except StopIteration:
        raise KeyError(f'Story {story_id} not found')

def add_story(story: Story):
    stories = get_stories()
    story.id = generate_id(stories)
    stories.append(story)
    write_stories(stories)
    return story


def update_story(story_id: str, story: Story):
    stories = get_stories()
    index = next(i for i, s in enumerate(stories) if s.id == story_id)
    story.id = story_id
    stories[index] = story
    write_stories(stories)
    return story


def clone_story(story_id: str):
    stories = get_stories()
    story = get_story(story_id, stories)

    cloned_story = story.model_copy()
    cloned_story.id = generate_id(stories)
    stories.append(cloned_story)
    write_stories(stories)
    return cloned_story


def delete_story(story_id: str):
    stories = get_stories()
    story = get_story(story_id, stories)

    stories.remove(story)
    delete_chapters(story_id)
    write_stories(stories)
    return story


def import_stories_from_webui(chats: list[WebUiChat]) -> list[Story]:
    imported = [convert_to_story(chat) for chat in chats]
    stories = get_stories()
    imported_stories = []
    for story, chapters in imported:
        story.id = generate_id(stories)
        imported_stories.append(story)
        write_chapters(story.id, chapters, ignore_checks=True)

    write_stories(stories + imported_stories)
    return imported_stories
