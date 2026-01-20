"""
Study service.

Handles study editing operations including move annotations.
Integrated with version service for automatic snapshots.
"""

import logging
from typing import TYPE_CHECKING, Optional
from ulid import ULID
from sqlalchemy.ext.asyncio import AsyncSession
import chess

from modules.workspace.db.repos.variation_repo import VariationRepository
from modules.workspace.db.tables.variations import MoveAnnotation
from modules.workspace.db.tables.variations import Variation
from modules.workspace.domain.models.variation import (
    AddMoveCommand,
    DeleteMoveCommand,
)
from modules.workspace.domain.models.move_annotation import (
    AddMoveAnnotationCommand,
    UpdateMoveAnnotationCommand,
    SetNAGCommand,
)
from modules.workspace.events.bus import EventBus
from modules.workspace.domain.services.pgn_sync_service import PgnSyncService
from backend.core.tagger.analysis.pipeline import AnalysisPipeline # New Import
from modules.workspace.pgn_v2.repo import PgnV2Repo # New Import
from modules.workspace.storage.r2_client import create_r2_client_from_env # New Import


class InvalidMoveError(Exception):
    """Raised when a move is invalid for the current position."""
    pass

if TYPE_CHECKING:
    from modules.workspace.domain.services.version_service import VersionService


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
    Optionally integrates with version service for automatic snapshots.
    """

    def __init__(
        self,
        session: AsyncSession,
        variation_repo: VariationRepository,
        event_bus: EventBus,
        pgn_sync_service: PgnSyncService | None = None,
        version_service: "VersionService | None" = None,
        analysis_pipeline: AnalysisPipeline | None = None, # New parameter
    ):
        """
        Initialize service.

        Args:
            session: Database session
            variation_repo: Variation repository
            event_bus: Event bus
            version_service: Optional version service for auto-snapshots
            analysis_pipeline: Optional AnalysisPipeline instance for tagger analysis
        """
        self.session = session
        self.variation_repo = variation_repo
        self.event_bus = event_bus
        self.pgn_sync_service = pgn_sync_service
        self.version_service = version_service
        self._operation_count = 0  # Track operations for auto-snapshot
        self._logger = logging.getLogger(__name__)

        if analysis_pipeline:
            self.analysis_pipeline = analysis_pipeline
        else:
            # Instantiate if not provided (e.g., for testing or direct use)
            r2_client = create_r2_client_from_env()
            pgn_v2_repo = PgnV2Repo(r2_client)
            self.analysis_pipeline = AnalysisPipeline(
                pgn_path="",  # Dummy path
                output_dir="/tmp",  # Dummy output dir
                pgn_v2_repo=pgn_v2_repo,
            )

    async def _sync_pgn(self, chapter_id: str) -> None:
        """
        Best-effort PGN sync after edits.

        This keeps R2 PGN up to date without blocking core write paths.
        """
        if not self.pgn_sync_service:
            return
        try:
            await self.pgn_sync_service.sync_chapter_pgn(chapter_id)
        except Exception as exc:
            self._logger.warning("PGN sync failed for %s: %s", chapter_id, exc)

    async def _run_tagger_analysis(self, chapter_id: str) -> None:
        """
        Best-effort tagger analysis after edits.
        """
        if not self.analysis_pipeline:
            self._logger.warning("AnalysisPipeline not configured, skipping tagger analysis for chapter %s", chapter_id)
            return
        try:
            # Need to re-fetch tree and fen_index as they might have been updated by pgn_sync
            # Create a new PgnV2Repo instance as it's not passed directly to _run_tagger_analysis
            pgn_v2_repo = PgnV2Repo(create_r2_client_from_env())
            
            try:
                fen_index = pgn_v2_repo.load_fen_index(chapter_id)
            except Exception as exc:
                self._logger.warning("FEN index missing for chapter %s: %s", chapter_id, exc)
                return
            tree_data = pgn_v2_repo.load_tree_json(chapter_id)
            if not _tree_data_has_fen(tree_data):
                tree_data = None

            await self.analysis_pipeline.run_fen_index_and_save(
                fen_index=fen_index,
                chapter_id=chapter_id,
                tree_data=tree_data,
                verbose=False,
            )
            self._logger.info("Tagger analysis completed for chapter %s", chapter_id)
        except Exception as exc:
            self._logger.warning("Tagger analysis failed for chapter %s: %s", chapter_id, exc)

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
            id=str(ULID()),
            move_id=command.move_id,
            nag=command.nag,
            text=command.text,
            author_id=command.author_id,
            version=1,
        )

        await self.variation_repo.create_annotation(annotation)
        await self.session.commit()
        await self._sync_pgn(move.chapter_id)
        await self._run_tagger_analysis(move.chapter_id) # Run tagger after sync

        # Check for auto-snapshot (requires study_id from chapter)
        # Note: This is a placeholder - real implementation needs chapter->study mapping
        # await self._check_and_create_auto_snapshot(
        #     study_id="TODO",
        #     actor_id=command.author_id,
        #     change_summary="Added move annotation"
        # )

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
        variation = await self.variation_repo.get_variation_by_id(annotation.move_id)
        if variation:
            await self._sync_pgn(variation.chapter_id)
            await self._run_tagger_analysis(variation.chapter_id) # Run tagger after sync

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
        variation = await self.variation_repo.get_variation_by_id(annotation.move_id)
        if variation:
            await self._sync_pgn(variation.chapter_id)
            await self._run_tagger_analysis(variation.chapter_id) # Run tagger after sync

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
            await self._sync_pgn(move.chapter_id)
            await self._run_tagger_analysis(move.chapter_id) # Run tagger after sync
            return existing
        else:
            # Create new annotation with just NAG
            annotation = MoveAnnotation(
                id=str(ULID()),
                move_id=command.move_id,
                nag=command.nag,
                text=None,
                author_id=command.actor_id,
                version=1,
            )
            await self.variation_repo.create_annotation(annotation)
            await self.session.commit()
            await self._sync_pgn(move.chapter_id)
            await self._run_tagger_analysis(move.chapter_id) # Run tagger after sync
            return annotation

    async def add_move(self, command: AddMoveCommand) -> Variation:
        """
        Add a move to the variation tree.

        Server-side FEN calculation: If fen is not provided, it will be computed
        from the parent position and the UCI move.

        Args:
            command: Add move command

        Returns:
            Created variation

        Raises:
            MoveNotFoundError: If parent move not found (when parent_id provided)
            InvalidMoveError: If the move is illegal for the position
        """
        parent_fen: Optional[str] = None

        # If parent_id provided, verify parent exists and get its FEN
        if command.parent_id:
            parent = await self.variation_repo.get_variation_by_id(
                command.parent_id
            )
            if not parent:
                raise MoveNotFoundError(
                    f"Parent move {command.parent_id} not found"
                )
            parent_fen = parent.fen
        else:
            # Root move - use standard starting position
            parent_fen = chess.STARTING_FEN

        # Compute FEN if not provided
        computed_fen = command.fen
        if not computed_fen and command.uci and parent_fen:
            computed_fen = self._compute_fen_after_move(parent_fen, command.uci)

        if not computed_fen:
            raise InvalidMoveError(
                f"Cannot compute FEN: missing parent FEN or UCI move"
            )

        # Create variation
        variation = Variation(
            id=str(ULID()),
            chapter_id=command.chapter_id,
            parent_id=command.parent_id,
            next_id=None,
            move_number=command.move_number,
            color=command.color,
            san=command.san,
            uci=command.uci,
            fen=computed_fen,
            rank=command.rank,
            priority=command.priority,
            visibility=command.visibility,
            pinned=False,
            created_by=command.created_by,
            version=1,
        )

        await self.variation_repo.create_variation(variation)
        await self.session.commit()
        await self._sync_pgn(command.chapter_id)
        await self._run_tagger_analysis(command.chapter_id) # Run tagger after sync

        return variation

    def _compute_fen_after_move(self, parent_fen: str, uci_move: str) -> str:
        """
        Compute the FEN after applying a UCI move to a position.

        Args:
            parent_fen: FEN of the position before the move
            uci_move: UCI notation of the move (e.g., "e2e4")

        Returns:
            FEN after the move

        Raises:
            InvalidMoveError: If the move is illegal
        """
        try:
            board = chess.Board(parent_fen)
            move = chess.Move.from_uci(uci_move)

            if move not in board.legal_moves:
                raise InvalidMoveError(
                    f"Illegal move {uci_move} in position {parent_fen}"
                )

            board.push(move)
            return board.fen()

        except ValueError as e:
            raise InvalidMoveError(f"Invalid UCI move format: {uci_move}") from e

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
        await self._sync_pgn(variation.chapter_id)
        await self._run_tagger_analysis(variation.chapter_id) # Run tagger after sync

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

    async def _check_and_create_auto_snapshot(
        self,
        study_id: str,
        actor_id: str,
        change_summary: str,
    ) -> None:
        """
        Check if auto-snapshot should be created and create it if needed.

        This method is called after significant operations (add/edit/delete moves).

        Args:
            study_id: Study ID
            actor_id: User who performed the operation
            change_summary: Brief description of the change
        """
        if self.version_service is None:
            # Version service not configured, skip auto-snapshot
            return

        # Increment operation count
        self._operation_count += 1

        # Check if snapshot should be created
        try:
            should_create = await self.version_service.should_create_auto_snapshot(
                study_id=study_id,
                operation_count=self._operation_count,
                time_threshold_minutes=5,
            )

            if should_create:
                # Create snapshot
                # Note: This requires capturing full study state
                # For now, we'll create a minimal snapshot
                # TODO: Implement full study state capture
                from modules.workspace.domain.models.version import (
                    CreateVersionCommand,
                    SnapshotContent,
                )

                snapshot_content = SnapshotContent(
                    version_number=0,  # Will be set by service
                    study_id=study_id,
                    study_data={"title": "Auto Snapshot"},  # TODO: Get actual data
                    chapters=[],  # TODO: Get actual chapters
                    variations=[],  # TODO: Get actual variations
                    annotations=[],  # TODO: Get actual annotations
                )

                await self.version_service.create_snapshot(
                    command=CreateVersionCommand(
                        study_id=study_id,
                        created_by=actor_id,
                        change_summary=f"Auto snapshot: {change_summary}",
                        is_rollback=False,
                    ),
                    snapshot_content=snapshot_content,
                )

                # Reset operation count after snapshot
                self._operation_count = 0

        except Exception as e:
            # Log error but don't fail the operation
            # Auto-snapshot is a nice-to-have feature
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to create auto-snapshot for study {study_id}: {e}"
            )


def _tree_data_has_fen(tree_data: dict) -> bool:
    nodes = tree_data.get("nodes", {})
    for node in nodes.values():
        if isinstance(node, dict) and "fen" in node:
            return True
    return False
