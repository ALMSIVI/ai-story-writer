from uuid import UUID

from pytest_mock import MockerFixture

from ai_story_writer.types import Chapter
from ai_story_writer.utils import id as id_utils


def test_generate_id_retries_collision(mocker: MockerFixture):
    existing = '00000000-0000-0000-0000-000000000001'
    new = '00000000-0000-0000-0000-000000000002'
    uuid4 = mocker.patch.object(id_utils, 'uuid4', side_effect=[UUID(existing), UUID(new)])

    result = id_utils.generate_id([Chapter(id=existing, outline='Outline')])

    assert result == new
    assert uuid4.call_count == 2
