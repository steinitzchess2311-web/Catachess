"""
Discussion reply repository.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.discussion_replies import DiscussionReply


class DiscussionReplyRepository:
    """Repository for discussion replies."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, reply: DiscussionReply) -> DiscussionReply:
        self.session.add(reply)
        await self.session.flush()
        return reply

    async def get_by_id(self, reply_id: str) -> DiscussionReply | None:
        stmt = select(DiscussionReply).where(DiscussionReply.id == reply_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_thread(self, thread_id: str) -> Sequence[DiscussionReply]:
        stmt = select(DiscussionReply).where(DiscussionReply.thread_id == thread_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, reply: DiscussionReply) -> DiscussionReply:
        await self.session.flush()
        await self.session.refresh(reply)
        return reply

    async def delete(self, reply: DiscussionReply) -> None:
        await self.session.delete(reply)
        await self.session.flush()
