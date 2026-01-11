"""
Discussion reaction repository.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.discussion_reactions import DiscussionReaction


class DiscussionReactionRepository:
    """Repository for discussion reactions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, reaction: DiscussionReaction
    ) -> DiscussionReaction:
        self.session.add(reaction)
        await self.session.flush()
        return reaction

    async def get_by_id(
        self, reaction_id: str
    ) -> DiscussionReaction | None:
        stmt = select(DiscussionReaction).where(
            DiscussionReaction.id == reaction_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_target(
        self, target_id: str, target_type: str
    ) -> Sequence[DiscussionReaction]:
        stmt = select(DiscussionReaction).where(
            DiscussionReaction.target_id == target_id,
            DiscussionReaction.target_type == target_type,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, reaction: DiscussionReaction) -> None:
        await self.session.delete(reaction)
        await self.session.flush()
