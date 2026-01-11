"""
Discussion thread repository.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.discussion_threads import DiscussionThread


class DiscussionThreadRepository:
    """Repository for discussion threads."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, thread: DiscussionThread) -> DiscussionThread:
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def get_by_id(self, thread_id: str) -> DiscussionThread | None:
        stmt = select(DiscussionThread).where(DiscussionThread.id == thread_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_target(
        self, target_id: str, target_type: str
    ) -> Sequence[DiscussionThread]:
        stmt = select(DiscussionThread).where(
            DiscussionThread.target_id == target_id,
            DiscussionThread.target_type == target_type,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, thread: DiscussionThread) -> DiscussionThread:
        await self.session.flush()
        await self.session.refresh(thread)
        return thread

    async def delete(self, thread: DiscussionThread) -> None:
        await self.session.delete(thread)
        await self.session.flush()
