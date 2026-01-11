"""
Study service.

Handles study editing operations including move annotations.
"""

from ulid import new as ulid_new
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.variation_repo import VariationRepository
from workspace.db.tables.variations import MoveAnnotation
from workspace.db.tables.variations import Variation
from workspace.domain.models.variation import (
    AddMoveCommand,
    DeleteMoveCommand,
)
from workspace.domain.models.move_annotation import (
    AddMoveAnnotationCommand,
    UpdateMoveAnnotationCommand,
    SetNAGCommand,
)
from workspace.events.bus import EventBus


class StudyServiceError(Exception):
    """Base exception for study service errors."""

    pass


class MoveNotFoundError(StudyServiceError):
    """Move not found."""

    pass


class AnnotationNotFoundError(StudyServiceError):
    """Annotation not found."""

    pass


class AnnotationAlreadyExistsError(StudyServiceError):
    """Annotation already exists for this move."""

    pass


class OptimisticLockError(StudyServiceError):
    """Optimistic lock conflict - resource was modified by another user."""

    pass


class StudyService:
    """
    Service for study editing operations.

    Handles move annotations and study tree modifications.
    """

    def __init__(
        self,
        session: AsyncSession,
        variation_repo: VariationRepository,
        event_bus: EventBus,
    ):
        """
        Initialize service.

        Args:
            session: Database session
            variation_repo: Variation repository
            event_bus: Event bus
        """
        self.session = session
        self.variation_repo = variation_repo
        self.event_bus = event_bus

    async def add_move_annotation(
        self, command: AddMoveAnnotationCommand
    ) -> MoveAnnotation:
        """
        Add annotation to a move.

        Args:
            command: Add annotation command

        Returns:
            Created move annotation

        Raises:
            MoveNotFoundError: If move not found
            AnnotationAlreadyExistsError: If annotation already exists for move
        """
        # Verify move exists
        move = await self.variation_repo.get_variation_by_id(command.move_id)
        if not move:
            raise MoveNotFoundError(f"Move {command.move_id} not found")

        # Check if annotation already exists
        existing = await self.variation_repo.get_annotation_for_move(
            command.move_id
        )
        if existing:
            raise AnnotationAlreadyExistsError(
                f"Annotation already exists for move {command.move_id}"
            )

        # Create annotation
        annotation = MoveAnnotation(
            id=str(ulid_new()),
            move_id=command.move_id,
            nag=command.nag,
            text=command.text,
            author_id=command.author_id,
            version=1,
        )

        await self.variation_repo.create_annotation(annotation)
        await self.session.commit()

        return annotation

    async def edit_move_annotation(
        self, command: UpdateMoveAnnotationCommand
    ) -> MoveAnnotation:
        """
        Edit an existing move annotation.

        Args:
            command: Update annotation command

        Returns:
            Updated move annotation

        Raises:
            AnnotationNotFoundError: If annotation not found
            OptimisticLockError: If version conflict detected
        """
        # Get annotation
        annotation = await self.variation_repo.get_annotation_by_id(
            command.annotation_id
        )
        if not annotation:
            raise AnnotationNotFoundError(
                f"Annotation {command.annotation_id} not found"
            )

        # Check optimistic lock
        if annotation.version != command.version:
            raise OptimisticLockError(
                f"Version conflict: expected {command.version}, "
                f"got {annotation.version}"
            )

        # Update fields
        annotation.nag = command.nag
        annotation.text = command.text

        await self.variation_repo.update_annotation(annotation)
        await self.session.commit()

        return annotation

    async def delete_move_annotation(
        self, annotation_id: str, actor_id: str
    ) -> None:
        """
        Delete a move annotation.

        Args:
            annotation_id: Annotation ID to delete
            actor_id: User ID performing deletion

        Raises:
            AnnotationNotFoundError: If annotation not found
        """
        # Get annotation
        annotation = await self.variation_repo.get_annotation_by_id(
            annotation_id
        )
        if not annotation:
            raise AnnotationNotFoundError(
                f"Annotation {annotation_id} not found"
            )

        await self.variation_repo.delete_annotation(annotation)
        await self.session.commit()

    async def set_nag(self, command: SetNAGCommand) -> MoveAnnotation:
        """
        Set or update NAG symbol for a move.

        Creates annotation if it doesn't exist, or updates existing one.

        Args:
            command: Set NAG command

        Returns:
            Created or updated move annotation

        Raises:
            MoveNotFoundError: If move not found
        """
        # Verify move exists
        move = await self.variation_repo.get_variation_by_id(command.move_id)
        if not move:
            raise MoveNotFoundError(f"Move {command.move_id} not found")

        # Check if annotation exists
        existing = await self.variation_repo.get_annotation_for_move(
            command.move_id
        )

        if existing:
            # Update existing annotation
            existing.nag = command.nag
            await self.variation_repo.update_annotation(existing)
            await self.session.commit()
            return existing
        else:
            # Create new annotation with just NAG
            annotation = MoveAnnotation(
                id=str(ulid_new()),
                move_id=command.move_id,
                nag=command.nag,
                text=None,
                author_id=command.actor_id,
                version=1,
            )
            await self.variation_repo.create_annotation(annotation)
            await self.session.commit()
            return annotation

    async def add_move(self, command: AddMoveCommand) -> Variation:
        """
        Add a move to the variation tree.

        Args:
            command: Add move command

        Returns:
            Created variation

        Raises:
            MoveNotFoundError: If parent move not found (when parent_id provided)
        """
        # If parent_id provided, verify parent exists
        if command.parent_id:
            parent = await self.variation_repo.get_variation_by_id(
                command.parent_id
            )
            if not parent:
                raise MoveNotFoundError(
                    f"Parent move {command.parent_id} not found"
                )

        # Create variation
        variation = Variation(
            id=str(ulid_new()),
            chapter_id=command.chapter_id,
            parent_id=command.parent_id,
            next_id=None,
            move_number=command.move_number,
            color=command.color,
            san=command.san,
            uci=command.uci,
            fen=command.fen,
            rank=command.rank,
            priority=command.priority,
            visibility=command.visibility,
            pinned=False,
            created_by=command.created_by,
            version=1,
        )

        await self.variation_repo.create_variation(variation)
        await self.session.commit()

        return variation

    async def delete_move(self, command: DeleteMoveCommand) -> None:
        """
        Delete a move and all its descendants.

        Args:
            command: Delete move command

        Raises:
            MoveNotFoundError: If move not found
        """
        # Get move to delete
        variation = await self.variation_repo.get_variation_by_id(
            command.variation_id
        )
        if not variation:
            raise MoveNotFoundError(
                f"Move {command.variation_id} not found"
            )

        # Recursively delete all descendants
        await self._delete_variation_recursive(variation)
        await self.session.commit()

    async def _delete_variation_recursive(self, variation: Variation) -> None:
        """
        Recursively delete a variation and all its descendants.

        Args:
            variation: Variation to delete
        """
        # Get all children
        children = await self.variation_repo.get_children(
            variation.id, variation.chapter_id
        )

        # Recursively delete children first
        for child in children:
            await self._delete_variation_recursive(child)

        # Delete this variation
        await self.variation_repo.delete_variation(variation)
