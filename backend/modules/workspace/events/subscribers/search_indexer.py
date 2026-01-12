"""
Search index subscriber for all searchable content.

Indexes:
- Discussion threads and replies
- Studies (node title + description)
- Chapters (title, white, black, event metadata)
- Move annotations (analytical text)
"""

from ulid import ULID

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.repos.search_index_repo import SearchIndexRepository
from workspace.db.repos.study_repo import StudyRepository
from workspace.db.repos.variation_repo import VariationRepository
from workspace.events.types import EventType


class SearchIndexer:
    """Update search index from content events."""

    def __init__(
        self,
        thread_repo: DiscussionThreadRepository,
        reply_repo: DiscussionReplyRepository,
        search_repo: SearchIndexRepository,
        node_repo: NodeRepository | None = None,
        study_repo: StudyRepository | None = None,
        variation_repo: VariationRepository | None = None,
    ) -> None:
        self.thread_repo = thread_repo
        self.reply_repo = reply_repo
        self.search_repo = search_repo
        self.node_repo = node_repo
        self.study_repo = study_repo
        self.variation_repo = variation_repo

    async def handle_event(self, event) -> None:
        # Discussion events
        if event.type in {
            EventType.DISCUSSION_THREAD_CREATED,
            EventType.DISCUSSION_THREAD_UPDATED,
        }:
            await self._index_thread(event.target_id)
        if event.type == EventType.DISCUSSION_THREAD_DELETED:
            await self._delete_entry(event.target_id, "discussion_thread")
        if event.type in {
            EventType.DISCUSSION_REPLY_ADDED,
            EventType.DISCUSSION_REPLY_EDITED,
        }:
            await self._index_reply(event.target_id)
        if event.type == EventType.DISCUSSION_REPLY_DELETED:
            await self._delete_entry(event.target_id, "discussion_reply")

        # Study events
        if event.type in {
            EventType.STUDY_CREATED,
            EventType.STUDY_UPDATED,
        }:
            await self._index_study(event.target_id)
        if event.type == EventType.STUDY_DELETED:
            await self._delete_entry(event.target_id, "study")

        # Chapter events
        if event.type in {
            EventType.STUDY_CHAPTER_CREATED,
            EventType.STUDY_CHAPTER_RENAMED,
        }:
            await self._index_chapter(event.target_id)
        if event.type == EventType.STUDY_CHAPTER_DELETED:
            await self._delete_entry(event.target_id, "chapter")

        # Move annotation events
        if event.type in {
            EventType.STUDY_MOVE_ANNOTATION_ADDED,
            EventType.STUDY_MOVE_ANNOTATION_UPDATED,
        }:
            await self._index_annotation(event.target_id)
        if event.type == EventType.STUDY_MOVE_ANNOTATION_DELETED:
            await self._delete_entry(event.target_id, "move_annotation")

    async def _index_thread(self, thread_id: str) -> None:
        thread = await self.thread_repo.get_by_id(thread_id)
        if not thread:
            return
        content = f"{thread.title}\n{thread.content}"
        await self.search_repo.upsert(
            entry_id=str(ULID()),
            target_id=thread.id,
            target_type="discussion_thread",
            content=content,
            author_id=thread.author_id,
        )

    async def _index_reply(self, reply_id: str) -> None:
        reply = await self.reply_repo.get_by_id(reply_id)
        if not reply:
            return
        await self.search_repo.upsert(
            entry_id=str(ULID()),
            target_id=reply.id,
            target_type="discussion_reply",
            content=reply.content,
            author_id=reply.author_id,
        )

    async def _delete_entry(self, target_id: str, target_type: str) -> None:
        await self.search_repo.delete_by_target(target_id, target_type)

    async def _index_study(self, study_id: str) -> None:
        """Index a study (node title + study description)."""
        if not self.node_repo or not self.study_repo:
            return
        # Get node data
        node = await self.node_repo.get_by_id(study_id)
        if not node:
            return

        # Get study data
        study = await self.study_repo.get_study_by_id(study_id)
        if not study:
            return

        # Combine title and description for indexing
        content_parts = [node.title]
        if study.description:
            content_parts.append(study.description)
        if study.tags:
            content_parts.append(study.tags)

        content = "\n".join(content_parts)

        await self.search_repo.upsert(
            entry_id=str(ULID()),
            target_id=study.id,
            target_type="study",
            content=content,
            author_id=node.owner_id,
        )

    async def _index_chapter(self, chapter_id: str) -> None:
        """Index a chapter (title + PGN metadata)."""
        if not self.study_repo or not self.node_repo:
            return
        chapter = await self.study_repo.get_chapter_by_id(chapter_id)
        if not chapter:
            return

        # Build searchable content from chapter metadata
        content_parts = [chapter.title]
        if chapter.white:
            content_parts.append(f"White: {chapter.white}")
        if chapter.black:
            content_parts.append(f"Black: {chapter.black}")
        if chapter.event:
            content_parts.append(f"Event: {chapter.event}")
        if chapter.date:
            content_parts.append(f"Date: {chapter.date}")

        content = "\n".join(content_parts)

        # Get study owner for author_id
        study = await self.study_repo.get_study_by_id(chapter.study_id)
        if not study:
            return

        node = await self.node_repo.get_by_id(study.id)
        if not node:
            return

        await self.search_repo.upsert(
            entry_id=str(ULID()),
            target_id=chapter.id,
            target_type="chapter",
            content=content,
            author_id=node.owner_id,
        )

    async def _index_annotation(self, annotation_id: str) -> None:
        """Index a move annotation (analytical text)."""
        if not self.variation_repo:
            return
        annotation = await self.variation_repo.get_annotation_by_id(annotation_id)
        if not annotation:
            return

        # Only index if there's text content
        if not annotation.text:
            return

        # Build content from NAG + text
        content_parts = []
        if annotation.nag:
            content_parts.append(f"NAG: {annotation.nag}")
        if annotation.text:
            content_parts.append(annotation.text)

        content = "\n".join(content_parts)

        await self.search_repo.upsert(
            entry_id=str(ULID()),
            target_id=annotation.id,
            target_type="move_annotation",
            content=content,
            author_id=annotation.author_id,
        )


def register_search_indexer(
    bus,
    thread_repo: DiscussionThreadRepository,
    reply_repo: DiscussionReplyRepository,
    node_repo: NodeRepository,
    study_repo: StudyRepository,
    variation_repo: VariationRepository,
    search_repo: SearchIndexRepository,
) -> SearchIndexer:
    """Register the search indexer subscriber on the bus."""
    indexer = SearchIndexer(
        thread_repo,
        reply_repo,
        search_repo,
        node_repo=node_repo,
        study_repo=study_repo,
        variation_repo=variation_repo,
    )
    bus.subscribe(indexer.handle_event)
    return indexer
