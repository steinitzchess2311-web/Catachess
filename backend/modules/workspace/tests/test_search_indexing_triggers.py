"""Tests for search index event triggers."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.repos.search_index_repo import SearchIndexRepository
from workspace.db.tables.discussion_replies import DiscussionReply
from workspace.db.tables.discussions import DiscussionThread
from workspace.events.bus import EventBus
from workspace.events.subscribers.search_indexer import SearchIndexer, register_search_indexer
from workspace.events.types import EventType


@pytest.fixture
async def event_bus() -> EventBus:
    """Create event bus."""
    return EventBus()


@pytest.fixture
async def thread_repo(session: AsyncSession) -> DiscussionThreadRepository:
    """Get thread repository."""
    return DiscussionThreadRepository(session)


@pytest.fixture
async def reply_repo(session: AsyncSession) -> DiscussionReplyRepository:
    """Get reply repository."""
    return DiscussionReplyRepository(session)


@pytest.fixture
async def search_repo(session: AsyncSession) -> SearchIndexRepository:
    """Get search index repository."""
    return SearchIndexRepository(session)


@pytest.fixture
async def search_indexer(
    event_bus: EventBus,
    thread_repo: DiscussionThreadRepository,
    reply_repo: DiscussionReplyRepository,
    search_repo: SearchIndexRepository,
) -> SearchIndexer:
    """Create and register search indexer."""
    return register_search_indexer(event_bus, thread_repo, reply_repo, search_repo)


@pytest.mark.asyncio
async def test_thread_created_triggers_index_update(
    event_bus: EventBus,
    thread_repo: DiscussionThreadRepository,
    search_repo: SearchIndexRepository,
    search_indexer: SearchIndexer,
    session: AsyncSession,
) -> None:
    """Test that creating a thread updates the search index."""
    # Create thread
    thread = DiscussionThread(
        id=str(uuid.uuid4()),
        target_id="study-123",
        target_type="study",
        author_id="user-1",
        title="Test Thread",
        content="This is searchable content",
        thread_type="question",
    )
    thread = await thread_repo.create(thread)
    await session.commit()

    # Emit event
    await event_bus.publish(
        event_type=EventType.DISCUSSION_THREAD_CREATED,
        actor_id="user-1",
        target_id=thread.id,
        target_type="discussion_thread",
        payload={"thread_id": thread.id},
    )

    # Verify index entry created
    results = await search_repo.search("searchable content")
    assert len(results) > 0
    assert any(r.target_id == thread.id for r in results)


@pytest.mark.asyncio
async def test_thread_updated_triggers_index_update(
    event_bus: EventBus,
    thread_repo: DiscussionThreadRepository,
    search_repo: SearchIndexRepository,
    search_indexer: SearchIndexer,
    session: AsyncSession,
) -> None:
    """Test that updating a thread updates the search index."""
    # Create and index thread
    thread = DiscussionThread(
        id=str(uuid.uuid4()),
        target_id="study-123",
        target_type="study",
        author_id="user-1",
        title="Original Title",
        content="Original content",
        thread_type="question",
    )
    thread = await thread_repo.create(thread)
    await session.commit()

    await event_bus.publish(
        event_type=EventType.DISCUSSION_THREAD_CREATED,
        actor_id="user-1",
        target_id=thread.id,
        target_type="discussion_thread",
        payload={},
    )

    # Update thread
    thread.title = "Updated Title"
    thread.content = "Updated searchable content"
    await session.commit()

    # Emit update event
    await event_bus.publish(
        event_type=EventType.DISCUSSION_THREAD_UPDATED,
        actor_id="user-1",
        target_id=thread.id,
        target_type="discussion_thread",
        payload={},
    )

    # Verify index updated with new content
    results = await search_repo.search("Updated searchable")
    assert len(results) > 0
    assert any(r.target_id == thread.id for r in results)


@pytest.mark.asyncio
async def test_thread_deleted_removes_from_index(
    event_bus: EventBus,
    thread_repo: DiscussionThreadRepository,
    search_repo: SearchIndexRepository,
    search_indexer: SearchIndexer,
    session: AsyncSession,
) -> None:
    """Test that deleting a thread removes it from the search index."""
    # Create and index thread
    thread = DiscussionThread(
        id=str(uuid.uuid4()),
        target_id="study-123",
        target_type="study",
        author_id="user-1",
        title="To Be Deleted",
        content="This will be removed",
        thread_type="question",
    )
    thread = await thread_repo.create(thread)
    await session.commit()

    await event_bus.publish(
        event_type=EventType.DISCUSSION_THREAD_CREATED,
        actor_id="user-1",
        target_id=thread.id,
        target_type="discussion_thread",
        payload={},
    )

    # Verify indexed
    initial_results = await search_repo.search("removed")
    assert len(initial_results) > 0

    # Delete thread
    await event_bus.publish(
        event_type=EventType.DISCUSSION_THREAD_DELETED,
        actor_id="user-1",
        target_id=thread.id,
        target_type="discussion_thread",
        payload={},
    )

    # Verify removed from index
    final_results = await search_repo.search("removed")
    assert not any(r.target_id == thread.id for r in final_results)


@pytest.mark.asyncio
async def test_reply_added_triggers_index_update(
    event_bus: EventBus,
    reply_repo: DiscussionReplyRepository,
    search_repo: SearchIndexRepository,
    search_indexer: SearchIndexer,
    session: AsyncSession,
) -> None:
    """Test that adding a reply updates the search index."""
    # Create reply
    reply = DiscussionReply(
        id=str(uuid.uuid4()),
        thread_id="thread-123",
        author_id="user-1",
        content="This is a searchable reply",
    )
    reply = await reply_repo.create(reply)
    await session.commit()

    # Emit event
    await event_bus.publish(
        event_type=EventType.DISCUSSION_REPLY_ADDED,
        actor_id="user-1",
        target_id=reply.id,
        target_type="discussion_reply",
        payload={},
    )

    # Verify index entry created
    results = await search_repo.search("searchable reply")
    assert len(results) > 0
    assert any(r.target_id == reply.id for r in results)


@pytest.mark.asyncio
async def test_reply_edited_triggers_index_update(
    event_bus: EventBus,
    reply_repo: DiscussionReplyRepository,
    search_repo: SearchIndexRepository,
    search_indexer: SearchIndexer,
    session: AsyncSession,
) -> None:
    """Test that editing a reply updates the search index."""
    # Create and index reply
    reply = DiscussionReply(
        id=str(uuid.uuid4()),
        thread_id="thread-123",
        author_id="user-1",
        content="Original reply content",
    )
    reply = await reply_repo.create(reply)
    await session.commit()

    await event_bus.publish(
        event_type=EventType.DISCUSSION_REPLY_ADDED,
        actor_id="user-1",
        target_id=reply.id,
        target_type="discussion_reply",
        payload={},
    )

    # Update reply
    reply.content = "Edited reply with new keywords"
    await session.commit()

    # Emit edit event
    await event_bus.publish(
        event_type=EventType.DISCUSSION_REPLY_EDITED,
        actor_id="user-1",
        target_id=reply.id,
        target_type="discussion_reply",
        payload={},
    )

    # Verify index updated
    results = await search_repo.search("new keywords")
    assert len(results) > 0
    assert any(r.target_id == reply.id for r in results)


@pytest.mark.asyncio
async def test_reply_deleted_removes_from_index(
    event_bus: EventBus,
    reply_repo: DiscussionReplyRepository,
    search_repo: SearchIndexRepository,
    search_indexer: SearchIndexer,
    session: AsyncSession,
) -> None:
    """Test that deleting a reply removes it from the search index."""
    # Create and index reply
    reply = DiscussionReply(
        id=str(uuid.uuid4()),
        thread_id="thread-123",
        author_id="user-1",
        content="Reply to be deleted",
    )
    reply = await reply_repo.create(reply)
    await session.commit()

    await event_bus.publish(
        event_type=EventType.DISCUSSION_REPLY_ADDED,
        actor_id="user-1",
        target_id=reply.id,
        target_type="discussion_reply",
        payload={},
    )

    # Verify indexed
    initial_results = await search_repo.search("deleted")
    assert len(initial_results) > 0

    # Delete reply
    await event_bus.publish(
        event_type=EventType.DISCUSSION_REPLY_DELETED,
        actor_id="user-1",
        target_id=reply.id,
        target_type="discussion_reply",
        payload={},
    )

    # Verify removed from index
    final_results = await search_repo.search("deleted")
    assert not any(r.target_id == reply.id for r in final_results)


@pytest.mark.asyncio
async def test_index_content_correctness(
    event_bus: EventBus,
    thread_repo: DiscussionThreadRepository,
    search_repo: SearchIndexRepository,
    search_indexer: SearchIndexer,
    session: AsyncSession,
) -> None:
    """Test that indexed content is correct (title + content for threads)."""
    # Create thread with distinct title and content
    thread = DiscussionThread(
        id=str(uuid.uuid4()),
        target_id="study-123",
        target_type="study",
        author_id="user-1",
        title="Unique Title Keyword",
        content="Unique Content Keyword",
        thread_type="question",
    )
    thread = await thread_repo.create(thread)
    await session.commit()

    await event_bus.publish(
        event_type=EventType.DISCUSSION_THREAD_CREATED,
        actor_id="user-1",
        target_id=thread.id,
        target_type="discussion_thread",
        payload={},
    )

    # Search for title keyword
    title_results = await search_repo.search("Unique Title")
    assert any(r.target_id == thread.id for r in title_results)

    # Search for content keyword
    content_results = await search_repo.search("Unique Content")
    assert any(r.target_id == thread.id for r in content_results)
