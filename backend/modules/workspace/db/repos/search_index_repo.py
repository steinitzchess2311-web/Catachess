"""
Search index repository.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.search_index import SearchIndex


class SearchIndexRepository:
    """Repository for search index entries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self, entry_id: str, target_id: str, target_type: str, content: str
    ) -> SearchIndex:
        stmt = select(SearchIndex).where(
            SearchIndex.target_id == target_id,
            SearchIndex.target_type == target_type,
        )
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry:
            entry.content = content
            await self.session.flush()
            return entry
        entry = SearchIndex(
            id=entry_id,
            target_id=target_id,
            target_type=target_type,
            content=content,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
