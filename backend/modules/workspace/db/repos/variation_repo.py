"""
Variation and MoveAnnotation repository for database operations.
"""

from typing import List, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace.db.tables.variations import MoveAnnotation, Variation


class VariationRepository:
    """
    Repository for Variation and MoveAnnotation database operations.

    Handles variation tree CRUD operations and move annotations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    # === Variation Operations ===

    async def create_variation(self, variation: Variation) -> Variation:
        """Create a new variation."""
        self.session.add(variation)
        await self.session.flush()
        return variation

    async def create_variations_bulk(self, variations: List[Variation]) -> None:
        """Bulk create new variations."""
        self.session.add_all(variations)
        await self.session.flush()

    async def get_variation_by_id(self, variation_id: str) -> Variation | None:
        """Get variation by ID."""
        stmt = select(Variation).where(Variation.id == variation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_variations_for_chapter(
        self, chapter_id: str
    ) -> Sequence[Variation]:
        """
        Get all variations for a chapter.

        Args:
            chapter_id: Chapter ID

        Returns:
            List of variations ordered by parent_id and rank
        """
        stmt = (
            select(Variation)
            .where(Variation.chapter_id == chapter_id)
            .order_by(Variation.parent_id, Variation.rank)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_children(
        self, parent_id: str | None, chapter_id: str
    ) -> Sequence[Variation]:
        """
        Get child variations for a parent move.

        Args:
            parent_id: Parent variation ID (None for root moves)
            chapter_id: Chapter ID

        Returns:
            List of child variations ordered by rank
        """
        stmt = (
            select(Variation)
            .where(
                and_(
                    Variation.parent_id == parent_id,
                    Variation.chapter_id == chapter_id,
                )
            )
            .order_by(Variation.rank)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_variation(self, variation: Variation) -> Variation:
        """Update a variation."""
        await self.session.flush()
        await self.session.refresh(variation)
        return variation

    async def delete_variation(self, variation: Variation) -> None:
        """Delete a variation (cascade deletes children)."""
        await self.session.delete(variation)
        await self.session.flush()

    async def reorder_siblings(
        self, parent_id: str | None, chapter_id: str, new_order: list[str]
    ) -> None:
        """
        Reorder sibling variations.

        Args:
            parent_id: Parent variation ID
            chapter_id: Chapter ID
            new_order: List of variation IDs in new order
        """
        for rank, var_id in enumerate(new_order):
            stmt = (
                select(Variation)
                .where(
                    and_(
                        Variation.id == var_id,
                        Variation.parent_id == parent_id,
                        Variation.chapter_id == chapter_id,
                    )
                )
            )
            result = await self.session.execute(stmt)
            variation = result.scalar_one_or_none()
            if variation:
                variation.rank = rank

        await self.session.flush()

    # === Move Annotation Operations ===

    async def create_annotation(
        self, annotation: MoveAnnotation
    ) -> MoveAnnotation:
        """Create a new move annotation."""
        self.session.add(annotation)
        await self.session.flush()
        return annotation

    async def create_annotations_bulk(self, annotations: List[MoveAnnotation]) -> None:
        """Bulk create new move annotations."""
        self.session.add_all(annotations)
        await self.session.flush()

    async def get_annotation_by_id(
        self, annotation_id: str
    ) -> MoveAnnotation | None:
        """Get annotation by ID."""
        stmt = select(MoveAnnotation).where(MoveAnnotation.id == annotation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_annotation_for_move(
        self, move_id: str
    ) -> MoveAnnotation | None:
        """
        Get annotation for a specific move.

        Args:
            move_id: Variation ID

        Returns:
            Move annotation or None if no annotation exists
        """
        stmt = select(MoveAnnotation).where(MoveAnnotation.move_id == move_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_annotations_for_chapter(
        self, chapter_id: str
    ) -> Sequence[MoveAnnotation]:
        """
        Get all annotations for variations in a chapter.

        Args:
            chapter_id: Chapter ID

        Returns:
            List of annotations
        """
        stmt = (
            select(MoveAnnotation)
            .join(Variation, MoveAnnotation.move_id == Variation.id)
            .where(Variation.chapter_id == chapter_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_annotation(
        self, annotation: MoveAnnotation
    ) -> MoveAnnotation:
        """Update a move annotation."""
        annotation.version += 1
        await self.session.flush()
        await self.session.refresh(annotation)
        return annotation

    async def delete_annotation(self, annotation: MoveAnnotation) -> None:
        """Delete a move annotation."""
        await self.session.delete(annotation)
        await self.session.flush()
