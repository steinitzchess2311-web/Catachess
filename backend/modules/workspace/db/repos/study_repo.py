"""
Study and Chapter repository for database operations.
"""

from typing import Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.studies import Chapter, Study


class StudyRepository:
    """
    Repository for Study database operations.

    Handles study and chapter CRUD operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    # === Study Operations ===

    async def create_study(self, study: Study) -> Study:
        """Create a new study."""
        self.session.add(study)
        await self.session.flush()
        return study

    async def get_study_by_id(self, study_id: str) -> Study | None:
        """Get study by ID."""
        stmt = select(Study).where(Study.id == study_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_study(self, study: Study) -> Study:
        """Update a study."""
        await self.session.flush()
        await self.session.refresh(study)
        return study

    async def delete_study(self, study: Study) -> None:
        """Delete a study (cascade deletes chapters)."""
        await self.session.delete(study)
        await self.session.flush()

    async def get_studies_by_node_ids(self, node_ids: list[str]) -> Sequence[Study]:
        """
        Get studies for multiple nodes.

        Args:
            node_ids: List of node IDs

        Returns:
            List of studies
        """
        stmt = select(Study).where(Study.id.in_(node_ids))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # === Chapter Operations ===

    async def create_chapter(self, chapter: Chapter) -> Chapter:
        """Create a new chapter."""
        self.session.add(chapter)
        await self.session.flush()
        return chapter

    async def get_chapter_by_id(self, chapter_id: str) -> Chapter | None:
        """Get chapter by ID."""
        stmt = select(Chapter).where(Chapter.id == chapter_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_chapter_by_r2_key(self, r2_key: str) -> Chapter | None:
        """Get chapter by R2 key."""
        stmt = select(Chapter).where(Chapter.r2_key == r2_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_chapters_for_study(
        self, study_id: str, order_by_order: bool = True
    ) -> Sequence[Chapter]:
        """
        Get all chapters for a study.

        Args:
            study_id: Study ID
            order_by_order: Sort by chapter order (default True)

        Returns:
            List of chapters
        """
        stmt = select(Chapter).where(Chapter.study_id == study_id)

        if order_by_order:
            stmt = stmt.order_by(Chapter.order)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_chapter(self, chapter: Chapter) -> Chapter:
        """Update a chapter."""
        await self.session.flush()
        await self.session.refresh(chapter)
        return chapter

    async def delete_chapter(self, chapter: Chapter) -> None:
        """Delete a chapter."""
        await self.session.delete(chapter)
        await self.session.flush()

    async def update_chapter_count(self, study_id: str) -> int:
        """
        Update chapter count for a study.

        Counts actual chapters and updates study.chapter_count.

        Args:
            study_id: Study ID

        Returns:
            Updated chapter count
        """
        # Count chapters
        chapters = await self.get_chapters_for_study(study_id, order_by_order=False)
        count = len(chapters)

        # Update study
        study = await self.get_study_by_id(study_id)
        if study:
            study.chapter_count = count
            await self.session.flush()

        return count

    async def reorder_chapters(
        self, study_id: str, chapter_order: list[str]
    ) -> None:
        """
        Reorder chapters in a study.

        Args:
            study_id: Study ID
            chapter_order: List of chapter IDs in desired order
        """
        for i, chapter_id in enumerate(chapter_order):
            chapter = await self.get_chapter_by_id(chapter_id)
            if chapter and chapter.study_id == study_id:
                chapter.order = i
                await self.session.flush()
