"""
Variation service.

Handles variation tree operations (promote, demote, reorder).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.variation_repo import VariationRepository
from workspace.domain.models.variation import (
    PromoteVariationCommand,
    DemoteVariationCommand,
    ReorderVariationsCommand,
)
from workspace.events.bus import EventBus


class VariationServiceError(Exception):
    """Base exception for variation service errors."""

    pass


class VariationNotFoundError(VariationServiceError):
    """Variation not found."""

    pass


class InvalidOperationError(VariationServiceError):
    """Invalid operation."""

    pass


class OptimisticLockError(VariationServiceError):
    """Optimistic lock conflict - resource was modified by another user."""

    pass


class VariationService:
    """
    Service for variation tree operations.

    Handles promote, demote, reorder operations on variation trees.
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

    async def promote_variation(
        self, command: PromoteVariationCommand
    ) -> None:
        """
        Promote a variation to main line.

        Swaps the ranks of the specified variation and the current main line.

        Args:
            command: Promote command

        Raises:
            VariationNotFoundError: If variation not found
            InvalidOperationError: If variation is already main line
            OptimisticLockError: If version conflict detected
        """
        # Get the variation to promote
        variation = await self.variation_repo.get_variation_by_id(
            command.variation_id
        )
        if not variation:
            raise VariationNotFoundError(
                f"Variation {command.variation_id} not found"
            )

        # Check optimistic lock version
        if command.expected_version is not None:
            if variation.version != command.expected_version:
                raise OptimisticLockError(
                    f"Version conflict: expected {command.expected_version}, "
                    f"got {variation.version}"
                )

        # Check if already main line
        if variation.rank == 0:
            raise InvalidOperationError("Variation is already main line")

        # Get all siblings (same parent)
        siblings = await self.variation_repo.get_children(
            variation.parent_id, variation.chapter_id
        )

        # Find current main line (rank 0)
        main_line = next((s for s in siblings if s.rank == 0), None)
        if not main_line:
            raise InvalidOperationError("No main line found")

        # Swap ranks and increment versions
        old_rank = variation.rank
        variation.rank = 0
        variation.version += 1
        main_line.rank = old_rank
        main_line.version += 1

        await self.variation_repo.update_variation(variation)
        await self.variation_repo.update_variation(main_line)
        await self.session.commit()

    async def demote_variation(
        self, command: DemoteVariationCommand
    ) -> None:
        """
        Demote a variation from main line to alternative.

        Swaps the ranks of the main line and the variation at target_rank.

        Args:
            command: Demote command

        Raises:
            VariationNotFoundError: If variation not found
            InvalidOperationError: If variation is not main line or target_rank invalid
            OptimisticLockError: If version conflict detected
        """
        # Get the variation to demote
        variation = await self.variation_repo.get_variation_by_id(
            command.variation_id
        )
        if not variation:
            raise VariationNotFoundError(
                f"Variation {command.variation_id} not found"
            )

        # Check optimistic lock version
        if command.expected_version is not None:
            if variation.version != command.expected_version:
                raise OptimisticLockError(
                    f"Version conflict: expected {command.expected_version}, "
                    f"got {variation.version}"
                )

        # Check if it's main line
        if variation.rank != 0:
            raise InvalidOperationError("Variation is not main line")

        # Validate target rank
        if command.target_rank <= 0:
            raise InvalidOperationError("Target rank must be greater than 0")

        # Get all siblings
        siblings = await self.variation_repo.get_children(
            variation.parent_id, variation.chapter_id
        )

        # Find variation at target rank
        target = next((s for s in siblings if s.rank == command.target_rank), None)
        if not target:
            raise InvalidOperationError(
                f"No variation found at rank {command.target_rank}"
            )

        # Swap ranks and increment versions
        variation.rank = command.target_rank
        variation.version += 1
        target.rank = 0
        target.version += 1

        await self.variation_repo.update_variation(variation)
        await self.variation_repo.update_variation(target)
        await self.session.commit()

    async def reorder_siblings(
        self, command: ReorderVariationsCommand
    ) -> None:
        """
        Reorder sibling variations.

        Sets the rank of each variation according to its position in new_order.

        Args:
            command: Reorder command with parent_id, chapter_id, and new_order

        Raises:
            VariationNotFoundError: If any variation not found
            InvalidOperationError: If variations are not siblings or list incomplete
        """
        # Get all current siblings
        siblings = await self.variation_repo.get_children(
            command.parent_id, command.chapter_id
        )

        # Validate all variations in new_order exist and are siblings
        sibling_ids = {s.id for s in siblings}
        if not all(vid in sibling_ids for vid in command.new_order):
            raise InvalidOperationError(
                "All variation IDs in new_order must be siblings"
            )

        # Validate new_order contains all siblings
        if len(command.new_order) != len(siblings):
            raise InvalidOperationError(
                f"new_order must contain all {len(siblings)} siblings"
            )

        # Use repository's reorder method
        await self.variation_repo.reorder_siblings(
            command.parent_id, command.chapter_id, command.new_order
        )
        await self.session.commit()
