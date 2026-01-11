"""
Tests for PGN clip service integration.
"""

import pytest

from workspace.db.repos.event_repo import EventRepository
from workspace.db.repos.study_repo import StudyRepository
from workspace.db.repos.variation_repo import VariationRepository
from workspace.db.tables.nodes import Node
from workspace.db.tables.studies import Chapter, Study
from workspace.db.tables.variations import (
    Variation,
    VariationPriority,
    VariationVisibility,
)
from workspace.domain.models.types import NodeType, Visibility
from workspace.domain.services.pgn_clip_service import PgnClipService
from workspace.events.types import EventType


@pytest.mark.asyncio
async def test_clip_service_emits_event(session, event_bus):
    node_id = "study-1"
    chapter_id = "chapter-1"

    node = Node(
        id=node_id,
        node_type=NodeType.STUDY,
        title="Test Study",
        description=None,
        owner_id="user-1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path=f"/{node_id}/",
        depth=0,
        layout={},
        version=1,
    )
    study = Study(
        id=node_id,
        description=None,
        chapter_count=1,
        is_public=False,
        tags=None,
    )
    chapter = Chapter(
        id=chapter_id,
        study_id=node_id,
        title="Chapter 1",
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

    move1 = Variation(
        id="v1",
        chapter_id=chapter_id,
        parent_id=None,
        next_id=None,
        move_number=1,
        color="white",
        san="e4",
        uci="e2e4",
        fen="fen1",
        rank=0,
        priority=VariationPriority.MAIN,
        visibility=VariationVisibility.PUBLIC,
        pinned=False,
        created_by="user-1",
        version=1,
    )
    move2 = Variation(
        id="v2",
        chapter_id=chapter_id,
        parent_id="v1",
        next_id=None,
        move_number=1,
        color="black",
        san="e5",
        uci="e7e5",
        fen="fen2",
        rank=0,
        priority=VariationPriority.MAIN,
        visibility=VariationVisibility.PUBLIC,
        pinned=False,
        created_by="user-1",
        version=1,
    )

    session.add_all([move1, move2])
    await session.flush()

    clip_service = PgnClipService(
        study_repo=StudyRepository(session),
        variation_repo=VariationRepository(session),
        event_repo=EventRepository(session),
        event_bus=event_bus,
    )

    result = await clip_service.clip_from_move(
        chapter_id=chapter_id,
        move_path="main.1",
        actor_id="user-1",
    )

    assert "e4" in result.pgn_text

    event_repo = EventRepository(session)
    events = await event_repo.get_events_for_target(chapter_id)
    assert len(events) == 1
    assert events[0].type == EventType.PGN_CLIPBOARD_GENERATED
