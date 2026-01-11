"""
Search index subscriber for discussion content.
"""

from ulid import new as ulid_new

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.repos.search_index_repo import SearchIndexRepository
from workspace.events.types import EventType


class SearchIndexer:
    """Update search index from discussion events."""

    def __init__(
        self,
        thread_repo: DiscussionThreadRepository,
        reply_repo: DiscussionReplyRepository,
        search_repo: SearchIndexRepository,
    ) -> None:
        self.thread_repo = thread_repo
        self.reply_repo = reply_repo
        self.search_repo = search_repo

    async def handle_event(self, event) -> None:
        if event.type in {
            EventType.DISCUSSION_THREAD_CREATED,
            EventType.DISCUSSION_THREAD_UPDATED,
        }:
            await self._index_thread(event.target_id)
        if event.type in {
            EventType.DISCUSSION_REPLY_ADDED,
            EventType.DISCUSSION_REPLY_EDITED,
        }:
            await self._index_reply(event.target_id)

    async def _index_thread(self, thread_id: str) -> None:
        thread = await self.thread_repo.get_by_id(thread_id)
        if not thread:
            return
        content = f"{thread.title}\n{thread.content}"
        await self.search_repo.upsert(
            entry_id=str(ulid_new()),
            target_id=thread.id,
            target_type="discussion_thread",
            content=content,
        )

    async def _index_reply(self, reply_id: str) -> None:
        reply = await self.reply_repo.get_by_id(reply_id)
        if not reply:
            return
        await self.search_repo.upsert(
            entry_id=str(ulid_new()),
            target_id=reply.id,
            target_type="discussion_reply",
            content=reply.content,
        )


def register_search_indexer(
    bus,
    thread_repo: DiscussionThreadRepository,
    reply_repo: DiscussionReplyRepository,
    search_repo: SearchIndexRepository,
) -> SearchIndexer:
    """Register the search indexer subscriber on the bus."""
    indexer = SearchIndexer(thread_repo, reply_repo, search_repo)
    bus.subscribe(indexer.handle_event)
    return indexer
