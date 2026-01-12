from datetime import UTC, datetime

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.search_index import SearchIndex


class SearchIndexRepository:
    """Repository for search index entries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        entry_id: str,
        target_id: str,
        target_type: str,
        content: str,
        author_id: str | None = None,
    ) -> SearchIndex:
        dialect = self.session.bind.dialect.name
        search_vector = (
            func.to_tsvector("english", content)
            if dialect == "postgresql"
            else content
        )
        stmt = select(SearchIndex).where(
            SearchIndex.target_id == target_id,
            SearchIndex.target_type == target_type,
        )
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry:
            entry.content = content
            entry.author_id = author_id
            entry.search_vector = search_vector
            entry.updated_at = datetime.now(UTC)
            await self.session.flush()
            return entry
        entry = SearchIndex(
            id=entry_id,
            target_id=target_id,
            target_type=target_type,
            author_id=author_id,
            content=content,
            search_vector=search_vector,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_by_target(
        self, target_id: str, target_type: str
    ) -> SearchIndex | None:
        stmt = select(SearchIndex).where(
            SearchIndex.target_id == target_id,
            SearchIndex.target_type == target_type,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_target(
        self, target_id: str, target_type: str
    ) -> None:
        stmt = delete(SearchIndex).where(
            SearchIndex.target_id == target_id,
            SearchIndex.target_type == target_type,
        )
        await self.session.execute(stmt)

    async def search(
        self,
        query: str,
        target_type: str | None = None,
        author_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SearchIndex]:
        stmt = select(SearchIndex)

        if target_type:
            stmt = stmt.where(SearchIndex.target_type == target_type)
        if author_id:
            stmt = stmt.where(SearchIndex.author_id == author_id)

        dialect = self.session.bind.dialect.name
        if dialect == "postgresql":
            ts_query = func.plainto_tsquery("english", query)
            stmt = stmt.where(SearchIndex.search_vector.op("@@")(ts_query))
            stmt = stmt.order_by(
                desc(func.ts_rank(SearchIndex.search_vector, ts_query)),
                desc(SearchIndex.updated_at),
            )
        else:
            stmt = stmt.where(SearchIndex.content.ilike(f"%{query}%"))
            stmt = stmt.order_by(desc(SearchIndex.updated_at))

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
