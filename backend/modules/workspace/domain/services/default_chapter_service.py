"""
Default chapter creation for newly created studies.
"""

import json
from datetime import datetime, timezone

from ulid import ULID

from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.tables.studies import Chapter as ChapterTable
from modules.workspace.events.bus import EventBus, publish_chapter_created
from modules.workspace.storage.keys import R2Keys
from modules.workspace.storage.r2_client import R2Client


DEFAULT_CHAPTER_TITLE = "Chapter 1"


def build_empty_chapter_tree() -> dict:
    """Return the empty tree.json payload used by a fresh study chapter."""
    return {
        "version": "v1",
        "rootId": "root",
        "nodes": {
            "root": {
                "id": "root",
                "parentId": None,
                "san": "",
                "children": [],
                "comment": None,
                "nags": [],
            },
        },
        "meta": {
            "result": "*",
        },
    }


async def ensure_default_chapter(
    *,
    study_id: str,
    actor_id: str,
    workspace_id: str | None,
    study_repo: StudyRepository,
    event_bus: EventBus,
    r2_client: R2Client,
) -> int:
    """
    Ensure a study has its initial chapter.

    Returns the current chapter count after the operation.
    """
    existing_chapters = await study_repo.get_chapters_for_study(study_id, order_by_order=True)
    if existing_chapters:
        return len(existing_chapters)

    chapter_id = str(ULID())
    r2_key = R2Keys.chapter_tree_json(chapter_id)
    upload_result = r2_client.upload_json(
        key=r2_key,
        content=json.dumps(build_empty_chapter_tree()),
        metadata={
            "study_id": study_id,
            "chapter_id": chapter_id,
            "order": "0",
        },
    )

    chapter = ChapterTable(
        id=chapter_id,
        study_id=study_id,
        title=DEFAULT_CHAPTER_TITLE,
        order=0,
        white=None,
        black=None,
        event=DEFAULT_CHAPTER_TITLE,
        date=None,
        result="*",
        r2_key=r2_key,
        pgn_hash=upload_result.content_hash,
        pgn_size=upload_result.size,
        pgn_status="ready",
        r2_etag=upload_result.etag,
        last_synced_at=datetime.now(timezone.utc),
    )

    await study_repo.create_chapter(chapter)
    count = await study_repo.update_chapter_count(study_id)
    await publish_chapter_created(
        event_bus,
        actor_id=actor_id,
        study_id=study_id,
        chapter_id=chapter_id,
        title=chapter.title,
        order=chapter.order,
        r2_key=r2_key,
        workspace_id=workspace_id,
    )
    return count
