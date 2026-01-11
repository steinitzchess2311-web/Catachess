"""
Discussion vs move annotation isolation test.
"""

import pytest

from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.tables.nodes import Node
from workspace.db.tables.studies import Chapter, Study
from workspace.db.tables.variations import MoveAnnotation, Variation, VariationPriority, VariationVisibility
from workspace.domain.models.discussion_thread import CreateThreadCommand
from workspace.domain.models.types import NodeType, Visibility
from workspace.domain.services.discussion.thread_service import ThreadService


@pytest.mark.asyncio
async def test_discussion_does_not_touch_move_annotations(session, event_bus):
    node = Node(
        id="study-1",
        node_type=NodeType.STUDY,
        title="Study",
        description=None,
        owner_id="user-1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/study-1/",
        depth=0,
        layout={},
        version=1,
    )
    study = Study(id="study-1", description=None, chapter_count=1, is_public=False, tags=None)
    chapter = Chapter(
        id="chapter-1",
        study_id="study-1",
        title="Chapter",
        order=0,
        white=None,
        black=None,
        event=None,
        date=None,
        result=None,
        r2_key="r2://chapter-1",
        pgn_hash=None,
        pgn_size=None,
        r2_etag=None,
        last_synced_at=None,
    )
    session.add_all([node, study, chapter])
    await session.flush()

    move = Variation(
        id="var-1",
        chapter_id="chapter-1",
        parent_id=None,
        next_id=None,
        move_number=1,
        color="white",
        san="e4",
        uci="e2e4",
        fen="fen",
        rank=0,
        priority=VariationPriority.MAIN,
        visibility=VariationVisibility.PUBLIC,
        pinned=False,
        created_by="user-1",
        version=1,
    )
    annotation = MoveAnnotation(
        id="anno-1",
        move_id="var-1",
        nag="!",
        text="Good move",
        author_id="user-1",
        version=1,
    )
    session.add_all([move, annotation])
    await session.flush()

    thread_repo = DiscussionThreadRepository(session)
    thread_service = ThreadService(session, thread_repo, event_bus)
    await thread_service.create_thread(
        CreateThreadCommand(
            target_id="study-1",
            target_type="study",
            author_id="user-2",
            title="Thread",
            content="Discussion text",
            thread_type="note",
        )
    )

    result = await session.get(MoveAnnotation, "anno-1")
    assert result is not None
