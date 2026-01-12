"""
PGN Clip Service - Domain service for PGN cleaning and exporting.

This service provides business logic for:
- Clipping PGN from a specific move (Phase 4 core innovation)
- Exporting PGN without comments
- Exporting raw mainline only
- Generating clipboard-ready PGN
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectionClosedError,
    EndpointConnectionError,
)

from workspace.db.repos.study_repo import StudyRepository
from workspace.db.repos.variation_repo import VariationRepository
from workspace.db.repos.event_repo import EventRepository
from workspace.events.bus import EventBus
from workspace.domain.models.event import CreateEventCommand
from workspace.events.types import EventType
from workspace.pgn.cleaner.pgn_cleaner import (
    clip_pgn_from_move,
    clip_pgn_from_move_to_clipboard,
    get_clip_preview,
)
from workspace.pgn.cleaner.no_comment_pgn import (
    export_no_comment_pgn,
    export_no_comment_pgn_to_clipboard,
)
from workspace.pgn.cleaner.raw_pgn import (
    export_raw_pgn,
    export_raw_pgn_to_clipboard,
    export_clean_mainline,
)
from workspace.pgn.serializer.to_tree import VariationNode, pgn_to_tree
from workspace.storage.r2_client import R2Client


@dataclass
class ClipResult:
    """
    Result of a PGN clip operation.

    Attributes:
        pgn_text: The clipped PGN text
        move_path: The path where clipping started
        moves_removed: Number of moves removed
        variations_removed: Number of variations removed
        timestamp: When the clip was generated
    """

    pgn_text: str
    move_path: str
    moves_removed: int
    variations_removed: int
    timestamp: datetime


@dataclass
class ExportResult:
    """
    Result of a PGN export operation.

    Attributes:
        pgn_text: The exported PGN text
        export_mode: The export mode used (clip, no_comment, raw, clean)
        timestamp: When the export was generated
    """

    pgn_text: str
    export_mode: str
    timestamp: datetime


class PgnClipService:
    """
    Service for PGN clipping and exporting.

    Responsibilities:
    - Clip PGN from specific moves
    - Export PGN in various modes
    - Generate clipboard-ready text
    - Emit events for tracking
    """

    def __init__(
        self,
        study_repo: StudyRepository,
        variation_repo: VariationRepository,
        event_repo: EventRepository,
        event_bus: EventBus,
        r2_client: R2Client,
        cache_ttl_seconds: int = 600,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.2,
    ):
        """
        Initialize PGN clip service.

        Args:
            study_repo: Study repository
            variation_repo: Variation repository
            event_repo: Event repository
            event_bus: Event bus for publishing events
        """
        self.study_repo = study_repo
        self.variation_repo = variation_repo
        self.event_bus = event_bus
        self.event_repo = event_repo
        self.r2_client = r2_client
        self._cache_ttl_seconds = cache_ttl_seconds
        self._max_retries = max_retries
        self._backoff_base_seconds = backoff_base_seconds
        self._tree_cache: dict[str, tuple[float, VariationNode]] = {}

    async def clip_from_move(
        self,
        chapter_id: str,
        move_path: str,
        actor_id: str,
        for_clipboard: bool = True,
    ) -> ClipResult:
        """
        Clip PGN starting from a specific move.

        Args:
            chapter_id: Chapter ID
            move_path: Path to the move to clip from (e.g., "main.12")
            actor_id: User ID performing the clip
            for_clipboard: If True, omit headers (for pasting)

        Returns:
            ClipResult with the clipped PGN and metadata

        Raises:
            ValueError: If chapter not found or move_path invalid
        """
        # Load chapter and build variation tree
        tree = await self._load_variation_tree(chapter_id)
        if tree is None:
            raise ValueError(f"Chapter {chapter_id} not found or has no moves")

        # Get preview to count removed items
        preview = get_clip_preview(tree, move_path)

        # Generate clipped PGN
        if for_clipboard:
            pgn_text = clip_pgn_from_move_to_clipboard(tree, move_path)
        else:
            # Load chapter metadata for headers
            chapter = await self.study_repo.get_chapter_by_id(chapter_id)
            headers = self._build_headers(chapter) if chapter else None
            pgn_text = clip_pgn_from_move(tree, move_path, headers=headers)

        # Emit event
        await self._emit_clipboard_event(
            chapter_id=chapter_id,
            actor_id=actor_id,
            export_mode="clip",
            move_path=move_path,
        )

        return ClipResult(
            pgn_text=pgn_text,
            move_path=move_path,
            moves_removed=preview["moves_before"],
            variations_removed=preview["variations_removed"],
            timestamp=datetime.now(UTC),
        )

    async def export_no_comments(
        self,
        chapter_id: str,
        actor_id: str,
        for_clipboard: bool = True,
    ) -> ExportResult:
        """
        Export PGN with variations but without comments.

        Args:
            chapter_id: Chapter ID
            actor_id: User ID performing the export
            for_clipboard: If True, omit headers

        Returns:
            ExportResult with the exported PGN

        Raises:
            ValueError: If chapter not found
        """
        # Load variation tree
        tree = await self._load_variation_tree(chapter_id)
        if tree is None:
            raise ValueError(f"Chapter {chapter_id} not found or has no moves")

        # Generate PGN
        if for_clipboard:
            pgn_text = export_no_comment_pgn_to_clipboard(tree)
        else:
            chapter = await self.study_repo.get_chapter_by_id(chapter_id)
            headers = self._build_headers(chapter) if chapter else None
            pgn_text = export_no_comment_pgn(tree, headers=headers)

        # Emit event
        await self._emit_clipboard_event(
            chapter_id=chapter_id,
            actor_id=actor_id,
            export_mode="no_comment",
        )

        return ExportResult(
            pgn_text=pgn_text,
            export_mode="no_comment",
            timestamp=datetime.now(UTC),
        )

    async def export_raw(
        self,
        chapter_id: str,
        actor_id: str,
        for_clipboard: bool = True,
    ) -> ExportResult:
        """
        Export raw PGN (mainline only).

        Args:
            chapter_id: Chapter ID
            actor_id: User ID performing the export
            for_clipboard: If True, omit headers

        Returns:
            ExportResult with the exported PGN

        Raises:
            ValueError: If chapter not found
        """
        # Load variation tree
        tree = await self._load_variation_tree(chapter_id)
        if tree is None:
            raise ValueError(f"Chapter {chapter_id} not found or has no moves")

        # Generate PGN
        if for_clipboard:
            pgn_text = export_raw_pgn_to_clipboard(tree)
        else:
            chapter = await self.study_repo.get_chapter_by_id(chapter_id)
            headers = self._build_headers(chapter) if chapter else None
            pgn_text = export_raw_pgn(tree, headers=headers)

        # Emit event
        await self._emit_clipboard_event(
            chapter_id=chapter_id,
            actor_id=actor_id,
            export_mode="raw",
        )

        return ExportResult(
            pgn_text=pgn_text,
            export_mode="raw",
            timestamp=datetime.now(UTC),
        )

    async def export_clean(
        self,
        chapter_id: str,
        actor_id: str,
    ) -> ExportResult:
        """
        Export clean mainline (no variations, no comments).

        Args:
            chapter_id: Chapter ID
            actor_id: User ID performing the export

        Returns:
            ExportResult with the exported PGN

        Raises:
            ValueError: If chapter not found
        """
        # Load variation tree
        tree = await self._load_variation_tree(chapter_id)
        if tree is None:
            raise ValueError(f"Chapter {chapter_id} not found or has no moves")

        # Generate PGN
        chapter = await self.study_repo.get_chapter_by_id(chapter_id)
        headers = self._build_headers(chapter) if chapter else None
        pgn_text = export_clean_mainline(tree, headers=headers)

        # Emit event
        await self._emit_clipboard_event(
            chapter_id=chapter_id,
            actor_id=actor_id,
            export_mode="clean",
        )

        return ExportResult(
            pgn_text=pgn_text,
            export_mode="clean",
            timestamp=datetime.now(UTC),
        )

    async def get_clip_preview(
        self,
        chapter_id: str,
        move_path: str,
    ) -> dict:
        """
        Get a preview of what will be clipped.

        Args:
            chapter_id: Chapter ID
            move_path: Path to clip from

        Returns:
            Dictionary with preview information

        Raises:
            ValueError: If chapter not found or move_path invalid
        """
        tree = await self._load_variation_tree(chapter_id)
        if tree is None:
            raise ValueError(f"Chapter {chapter_id} not found or has no moves")

        return get_clip_preview(tree, move_path)

    async def _load_variation_tree(self, chapter_id: str) -> VariationNode | None:
        """
        Load variation tree from R2 storage.

        Args:
            chapter_id: Chapter ID

        Returns:
            Root VariationNode, or None if no moves

        Note:
            Uses in-memory caching to avoid repeated R2 downloads.
        """
        cached = self._tree_cache.get(chapter_id)
        if cached:
            expires_at, cached_tree = cached
            if time.monotonic() < expires_at:
                return cached_tree
            self._tree_cache.pop(chapter_id, None)

        chapter = await self.study_repo.get_chapter_by_id(chapter_id)
        if not chapter or not chapter.r2_key:
            return None

        pgn_text = None
        for attempt in range(1, self._max_retries + 1):
            try:
                pgn_text = self.r2_client.download_pgn(chapter.r2_key)
                break
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code in {"404", "NoSuchKey"}:
                    raise ValueError(
                        f"PGN not found for chapter {chapter_id}"
                    ) from exc
                if attempt >= self._max_retries:
                    raise ValueError(
                        "Failed to load PGN from storage"
                    ) from exc
            except (
                EndpointConnectionError,
                ConnectionClosedError,
                BotoCoreError,
            ) as exc:
                if attempt >= self._max_retries:
                    raise ValueError(
                        "Failed to load PGN from storage"
                    ) from exc
            if attempt < self._max_retries and self._backoff_base_seconds > 0:
                await asyncio.sleep(
                    self._backoff_base_seconds * (2 ** (attempt - 1))
                )

        if pgn_text is None:
            raise ValueError("Failed to load PGN from storage")

        tree = pgn_to_tree(pgn_text)
        if tree is None:
            raise ValueError("Invalid PGN content")

        if self._cache_ttl_seconds > 0:
            self._tree_cache[chapter_id] = (
                time.monotonic() + self._cache_ttl_seconds,
                tree,
            )

        return tree

    def _build_headers(self, chapter: any) -> dict[str, str]:
        """
        Build PGN headers from chapter metadata.

        Args:
            chapter: Chapter object

        Returns:
            Dictionary of PGN headers
        """
        # Basic headers
        headers = {
            "Event": getattr(chapter, "title", "Study Chapter"),
            "Site": "CataChess",
            "Date": datetime.now(UTC).strftime("%Y.%m.%d"),
            "Round": "?",
            "White": "?",
            "Black": "?",
            "Result": "*",
        }

        return headers

    async def _emit_clipboard_event(
        self,
        chapter_id: str,
        actor_id: str,
        export_mode: str,
        move_path: str | None = None,
    ) -> None:
        """
        Emit clipboard generated event.

        Args:
            chapter_id: Chapter ID
            actor_id: User ID
            export_mode: Export mode (clip, no_comment, raw, clean)
            move_path: Move path (for clip mode)
        """
        payload = {
            "chapter_id": chapter_id,
            "export_mode": export_mode,
        }

        if move_path:
            payload["move_path"] = move_path

        latest_version = await self.event_repo.get_latest_version(chapter_id)
        command = CreateEventCommand(
            type=EventType.PGN_CLIPBOARD_GENERATED,
            actor_id=actor_id,
            target_id=chapter_id,
            target_type="chapter",
            version=latest_version + 1,
            payload=payload,
        )

        await self.event_bus.publish(command)
