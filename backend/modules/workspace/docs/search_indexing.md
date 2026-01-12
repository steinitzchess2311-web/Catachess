# Search Indexing Architecture

This document describes how the search index is maintained through event-driven updates.

## Overview

The Workspace system uses **event-driven search indexing** to keep search results up-to-date. Instead of polling or scheduled batch updates, the search index is updated in real-time as content changes occur.

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Write     │ ─emit─> │   Event      │ ─sub──> │   Search     │
│  Operation  │         │     Bus      │         │   Indexer    │
└─────────────┘         └──────────────┘         └──────────────┘
                                                         │
                                                    ┌────▼─────┐
                                                    │  Search  │
                                                    │   Index  │
                                                    │    DB    │
                                                    └──────────┘
```

## Indexed Content

The search index includes the following content types:

### 1. Discussion Threads

**Indexed Fields:**
- Thread title
- Thread content
- Author ID
- Target object ID

**Triggering Events:**
- `discussion.thread.created` → Create index entry
- `discussion.thread.updated` → Update index entry
- `discussion.thread.deleted` → Delete index entry

**Index Key:** `discussion_thread:{thread_id}`

### 2. Discussion Replies

**Indexed Fields:**
- Reply content
- Author ID
- Parent thread ID

**Triggering Events:**
- `discussion.reply.added` → Create index entry
- `discussion.reply.edited` → Update index entry
- `discussion.reply.deleted` → Delete index entry

**Index Key:** `discussion_reply:{reply_id}`

### 3. Study Metadata (Future)

**Indexed Fields:**
- Study title
- Study description
- Tags
- Author ID

**Triggering Events:**
- `study.created` → Create index entry
- `study.updated` → Update index entry
- `study.deleted` → Delete index entry

### 4. Chapter Titles (Future)

**Indexed Fields:**
- Chapter title
- Study ID
- Chapter order

**Triggering Events:**
- `study.chapter.created` → Create index entry
- `study.chapter.renamed` → Update index entry
- `study.chapter.deleted` → Delete index entry

### 5. Move Annotations (Future)

**Indexed Fields:**
- Annotation text
- NAG symbols
- Chapter ID
- Move path

**Triggering Events:**
- `study.move_annotation.added` → Create index entry
- `study.move_annotation.updated` → Update index entry
- `study.move_annotation.deleted` → Delete index entry

## Event Subscriber Implementation

The `SearchIndexer` class subscribes to relevant events:

```python
# Located at: events/subscribers/search_indexer.py

class SearchIndexer:
    """Update search index from discussion events."""

    async def handle_event(self, event) -> None:
        # Thread events
        if event.type in {
            EventType.DISCUSSION_THREAD_CREATED,
            EventType.DISCUSSION_THREAD_UPDATED,
        }:
            await self._index_thread(event.target_id)

        if event.type == EventType.DISCUSSION_THREAD_DELETED:
            await self._delete_entry(event.target_id, "discussion_thread")

        # Reply events
        if event.type in {
            EventType.DISCUSSION_REPLY_ADDED,
            EventType.DISCUSSION_REPLY_EDITED,
        }:
            await self._index_reply(event.target_id)

        if event.type == EventType.DISCUSSION_REPLY_DELETED:
            await self._delete_entry(event.target_id, "discussion_reply")
```

## Search Index Table Schema

```sql
CREATE TABLE search_index (
    id VARCHAR(64) PRIMARY KEY,
    target_id VARCHAR(64) NOT NULL,
    target_type VARCHAR(64) NOT NULL,  -- 'discussion_thread', 'discussion_reply', etc.
    content TEXT NOT NULL,             -- Full-text searchable content
    author_id VARCHAR(64),             -- For permission filtering
    search_vector tsvector,            -- PostgreSQL full-text search
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    INDEX idx_target (target_id, target_type),
    INDEX idx_author (author_id),
    INDEX idx_search_vector USING GIN (search_vector)
);
```

## Search Query Flow

1. **User submits search query**
2. **Query is parsed** and converted to tsquery
3. **Full-text search** executed on `search_vector` column
4. **Results are filtered** by user permissions (see [Privacy Rules](./privacy_rules.md))
5. **Results are ranked** by relevance
6. **Results are returned** with highlights

## Rebuilding the Index

If the search index becomes corrupted or out of sync, it can be rebuilt:

### Manual Rebuild

```python
# scripts/rebuild_search_index.py

async def rebuild_search_index():
    """Rebuild the entire search index from scratch."""
    # Clear existing index
    await search_repo.truncate()

    # Reindex all threads
    threads = await thread_repo.list_all()
    for thread in threads:
        await indexer._index_thread(thread.id)

    # Reindex all replies
    replies = await reply_repo.list_all()
    for reply in replies:
        await indexer._index_reply(reply.id)

    # Future: Reindex studies, chapters, annotations
```

### Background Job

For large datasets, use a background job:

```python
# jobs/search_reindex_job.py

async def search_reindex_job():
    """Background job to rebuild search index."""
    # Process in batches to avoid memory issues
    batch_size = 1000
    offset = 0

    while True:
        batch = await get_indexable_content(offset, batch_size)
        if not batch:
            break

        for item in batch:
            await index_item(item)

        offset += batch_size
```

## Performance Considerations

### Index Updates

- **Async**: Index updates are asynchronous and don't block the main request
- **Error Handling**: Failed index updates are logged but don't fail the main operation
- **Idempotent**: Index operations are idempotent (upsert, not insert)

### Search Queries

- **Pagination**: All search queries should be paginated
- **Limits**: Set reasonable result limits (e.g., max 1000 results)
- **Caching**: Consider caching popular search queries

### Index Size

- **Monitoring**: Monitor index table size
- **Cleanup**: Soft-deleted content should be removed from index
- **Archival**: Consider archiving old entries

## Testing

All search indexing functionality must be tested:

```python
# tests/test_search_indexing_triggers.py

async def test_thread_created_updates_index():
    """Test that creating a thread updates the search index."""
    # Create thread
    thread = await service.create_thread(...)

    # Verify index entry created
    results = await search_repo.search("thread content")
    assert thread.id in [r.target_id for r in results]


async def test_reply_deleted_removes_from_index():
    """Test that deleting a reply removes it from the index."""
    # Create and delete reply
    reply = await service.add_reply(...)
    await service.delete_reply(reply.id)

    # Verify index entry deleted
    results = await search_repo.search("reply content")
    assert reply.id not in [r.target_id for r in results]
```

## Event-to-Index Mapping

Complete list of events that trigger index updates:

| Event Type | Action | Content Type |
|------------|--------|--------------|
| `discussion.thread.created` | Insert | discussion_thread |
| `discussion.thread.updated` | Update | discussion_thread |
| `discussion.thread.deleted` | Delete | discussion_thread |
| `discussion.reply.added` | Insert | discussion_reply |
| `discussion.reply.edited` | Update | discussion_reply |
| `discussion.reply.deleted` | Delete | discussion_reply |
| `study.created` | Insert | study (future) |
| `study.updated` | Update | study (future) |
| `study.deleted` | Delete | study (future) |
| `study.chapter.created` | Insert | chapter (future) |
| `study.chapter.renamed` | Update | chapter (future) |
| `study.chapter.deleted` | Delete | chapter (future) |
| `study.move_annotation.added` | Insert | annotation (future) |
| `study.move_annotation.updated` | Update | annotation (future) |
| `study.move_annotation.deleted` | Delete | annotation (future) |

## Troubleshooting

### Index Not Updating

1. **Check event bus**: Verify events are being published
2. **Check subscriber**: Verify SearchIndexer is registered
3. **Check logs**: Look for indexing errors
4. **Rebuild index**: Use manual rebuild script

### Search Results Outdated

1. **Check event processing**: Ensure events are processed in order
2. **Check database**: Verify index table contains recent updates
3. **Clear cache**: If using query cache, clear it

### Performance Issues

1. **Check index size**: Large indexes may need optimization
2. **Analyze queries**: Use EXPLAIN to analyze slow queries
3. **Update statistics**: Run ANALYZE on search_index table
4. **Consider partitioning**: For very large datasets

## Related Documentation

- [Event System](./event_system.md)
- [Privacy Rules](./privacy_rules.md)
- [Discussion System](./discussion_system.md)
