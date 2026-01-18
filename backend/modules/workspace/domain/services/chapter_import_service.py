"""
Chapter import service.

Handles PGN import, chapter detection, auto-splitting, and R2 storage.
"""

from datetime import datetime, timezone
from ulid import ULID

from modules.workspace.db.repos.node_repo import NodeRepository
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.tables.nodes import Node as NodeTable
from modules.workspace.db.tables.studies import Chapter as ChapterTable
from modules.workspace.db.tables.studies import Study as StudyTable
from modules.workspace.domain.models.node import CreateNodeCommand, NodeModel
from modules.workspace.domain.models.study import CreateStudyCommand, ImportPGNCommand, ImportResult
from modules.workspace.domain.models.types import NodeType, Visibility
from modules.workspace.domain.services.node_service import NodeNotFoundError, NodeService
from modules.workspace.events.bus import EventBus, publish_study_created, publish_chapter_imported
from core.new_pgn import PGNGame, detect_games
from modules.workspace.pgn.chapter_detector import detect_chapters, split_games_into_studies, suggest_study_names
from modules.workspace.pgn.parser.normalize import normalize_pgn
from modules.workspace.storage.integrity import calculate_sha256, calculate_size
from modules.workspace.storage.keys import R2Keys
from modules.workspace.storage.r2_client import R2Client


class ChapterImportError(Exception):
    """Base exception for chapter import errors."""

    pass


class StudyFullError(ChapterImportError):
    """Study has reached 64-chapter limit."""

    pass


class ChapterImportService:
    """
    Service for importing PGN content into studies.

    Handles:
    - PGN parsing and normalization
    - Chapter detection and auto-splitting
    - Study and chapter creation
    - R2 storage upload
    - Event publishing
    """

    def __init__(
        self,
        node_service: NodeService,
        node_repo: NodeRepository,
        study_repo: StudyRepository,
        r2_client: R2Client,
        event_bus: EventBus,
    ):
        """
        Initialize service.

        Args:
            node_service: Node service for node operations
            node_repo: Node repository
            study_repo: Study repository
            r2_client: R2 storage client
            event_bus: Event bus for publishing
        """
        self.node_service = node_service
        self.node_repo = node_repo
        self.study_repo = study_repo
        self.r2_client = r2_client
        self.event_bus = event_bus

    async def import_pgn(
        self, command: ImportPGNCommand, actor_id: str
    ) -> ImportResult:
        """
        Import PGN content, creating studies and chapters.

        Workflow:
        1. Normalize and parse PGN
        2. Detect chapters and determine if split needed
        3. If <= 64: Create single study
        4. If > 64 and auto_split: Create folder + multiple studies
        5. Upload chapters to R2
        6. Create chapter records in DB
        7. Publish events

        Args:
            command: Import command
            actor_id: User performing import

        Returns:
            ImportResult with created studies

        Raises:
            ChapterImportError: If import fails
        """
        # Step 1: Normalize PGN
        normalized = normalize_pgn(command.pgn_content)

        # Step 2: Detect chapters
        detection = detect_chapters(normalized, fast=False)

        # Step 3: Split games
        all_games = detect_games(normalized)
        if not all_games:
            raise ChapterImportError("No games found in PGN content")

        if detection.is_single_study:
            # Single study workflow
            return await self._import_single_study(
                command, all_games, actor_id
            )
        else:
            # Multi-study workflow (split)
            if not command.auto_split:
                raise ChapterImportError(
                    f"PGN has {detection.total_chapters} chapters (> 64). "
                    "Enable auto_split to create multiple studies."
                )

            return await self._import_multi_study(
                command, all_games, detection, actor_id
            )

    async def import_pgn_into_study(
        self, study_id: str, pgn_content: str, actor_id: str
    ) -> ImportResult:
        """
        Import PGN content into an existing study as new chapters.

        Returns:
            ImportResult with created studies.
        """
        node = await self.node_repo.get_by_id(study_id, include_deleted=True)
        if not node or node.node_type != NodeType.STUDY:
            raise NodeNotFoundError(f"Study node {study_id} not found")

        normalized = normalize_pgn(pgn_content)
        detection = detect_chapters(normalized, fast=False)
        games = detect_games(normalized)
        if not games:
            raise ChapterImportError("No games found in PGN content")

        if detection.requires_split:
            command = ImportPGNCommand(
                parent_id=node.parent_id,
                owner_id=node.owner_id,
                pgn_content=normalized,
                base_title=node.title,
                auto_split=True,
                visibility=node.visibility,
            )
            return await self._import_multi_study(command, games, detection, actor_id)

        # Enforce 64 chapter limit for single-study import
        existing = await self.study_repo.get_chapters_for_study(
            study_id, order_by_order=False
        )
        total = len(existing) + len(games)
        if total > 64:
            raise StudyFullError(
                f"Study has {len(existing)} chapters. "
                f"Import would exceed limit (64)."
            )

        await self._add_chapters_to_study(study_id, games, actor_id)
        return ImportResult(
            total_chapters=detection.total_chapters,
            studies_created=[study_id],
            folder_id=None,
            was_split=False,
        )

    async def _import_single_study(
        self,
        command: ImportPGNCommand,
        games: list[PGNGame],
        actor_id: str,
    ) -> ImportResult:
        """
        Import PGN into single study.

        Args:
            command: Import command
            games: Parsed games
            actor_id: Actor ID

        Returns:
            ImportResult
        """
        # Create study node
        study_node = await self._create_study_node(
            title=command.base_title,
            owner_id=command.owner_id,
            parent_id=command.parent_id,
            visibility=command.visibility,
            actor_id=actor_id,
        )

        # Create study entity
        study = await self._create_study_entity(study_node.id)

        # Add chapters
        await self._add_chapters_to_study(study.id, games, actor_id)

        # Publish event
        await publish_study_created(
            self.event_bus,
            actor_id=actor_id,
            study_id=study.id,
            title=command.base_title,
            chapter_count=len(games),
            workspace_id=self._get_workspace_id(study_node.path),
        )

        return ImportResult(
            total_chapters=len(games),
            studies_created=[study.id],
            folder_id=None,
            was_split=False,
        )

    async def _import_multi_study(
        self,
        command: ImportPGNCommand,
        all_games: list[PGNGame],
        detection,
        actor_id: str,
    ) -> ImportResult:
        """
        Import PGN into multiple studies (split workflow).

        Creates a folder containing multiple studies.

        Args:
            command: Import command
            all_games: All parsed games
            detection: Chapter detection result
            actor_id: Actor ID

        Returns:
            ImportResult
        """
        # Create folder to hold studies
        folder_node = await self._create_folder_node(
            title=f"{command.base_title} (Collection)",
            owner_id=command.owner_id,
            parent_id=command.parent_id,
            visibility=command.visibility,
            actor_id=actor_id,
        )

        # Split games into studies
        study_games = split_games_into_studies(
            all_games, detection.chapters_per_study
        )

        # Generate study names
        study_names = suggest_study_names(
            command.base_title,
            detection.num_studies,
            detection.chapters_per_study,
        )

        # Create each study
        created_study_ids = []
        for study_name, games in zip(study_names, study_games):
            # Create study node
            study_node = await self._create_study_node(
                title=study_name,
                owner_id=command.owner_id,
                parent_id=folder_node.id,
                visibility=command.visibility,
                actor_id=actor_id,
            )

            # Create study entity
            study = await self._create_study_entity(study_node.id)

            # Add chapters
            await self._add_chapters_to_study(study.id, games, actor_id)

            # Publish event
            await publish_study_created(
                self.event_bus,
                actor_id=actor_id,
                study_id=study.id,
                title=study_name,
                chapter_count=len(games),
                workspace_id=self._get_workspace_id(study_node.path),
            )

            created_study_ids.append(study.id)

        return ImportResult(
            total_chapters=len(all_games),
            studies_created=created_study_ids,
            folder_id=folder_node.id,
            was_split=True,
        )

    async def _create_study_node(
        self,
        title: str,
        owner_id: str,
        parent_id: str | None,
        visibility: Visibility,
        actor_id: str,
    ) -> NodeModel:
        """Create a study node."""
        command = CreateNodeCommand(
            node_type=NodeType.STUDY,
            title=title,
            owner_id=owner_id,
            parent_id=parent_id,
            visibility=visibility,
        )

        node = await self.node_service.create_node(command, actor_id)
        return node

    async def _create_folder_node(
        self,
        title: str,
        owner_id: str,
        parent_id: str | None,
        visibility: Visibility,
        actor_id: str,
    ) -> NodeModel:
        """Create a folder node."""
        command = CreateNodeCommand(
            node_type=NodeType.FOLDER,
            title=title,
            owner_id=owner_id,
            parent_id=parent_id,
            visibility=visibility,
        )

        node = await self.node_service.create_node(command, actor_id)
        return node

    async def _create_study_entity(self, study_id: str) -> StudyTable:
        """Create study entity in database."""
        study = StudyTable(
            id=study_id,
            description=None,
            chapter_count=0,
            is_public=False,
            tags=None,
        )

        return await self.study_repo.create_study(study)

    async def _add_chapters_to_study(
        self, study_id: str, games: list[PGNGame], actor_id: str
    ) -> None:
        """
        Add chapters to study.

        Uploads PGN to R2 and creates chapter records.

        Args:
            study_id: Study ID
            games: List of games
            actor_id: Actor ID
        """
        for i, game in enumerate(games):
            # Generate chapter ID
            chapter_id = str(ULID())

            # Generate R2 key
            r2_key = R2Keys.chapter_pgn(chapter_id)

            # Upload to R2
            upload_result = self.r2_client.upload_pgn(
                key=r2_key,
                content=game.raw,
                metadata={
                    "study_id": study_id,
                    "chapter_id": chapter_id,
                    "order": str(i),
                },
            )

            # Create chapter record
            chapter = ChapterTable(
                id=chapter_id,
                study_id=study_id,
                title=self._header_value(game, "Event", f"Chapter {i + 1}"),
                order=i,
                white=self._header_value(game, "White", "?"),
                black=self._header_value(game, "Black", "?"),
                event=self._header_value(game, "Event", "Unknown"),
                date=self._header_value(game, "Date", "????.??.??"),
                result=self._header_value(game, "Result", "*"),
                r2_key=r2_key,
                pgn_hash=upload_result.content_hash,
                pgn_size=upload_result.size,
                r2_etag=upload_result.etag,
                last_synced_at=datetime.now(timezone.utc),
            )

            await self.study_repo.create_chapter(chapter)

            # Publish event
            await publish_chapter_imported(
                self.event_bus,
                actor_id=actor_id,
                study_id=study_id,
                chapter_id=chapter_id,
                title=chapter.title,
                order=i,
                r2_key=r2_key,
                workspace_id=await self._get_workspace_id_for_study(study_id),
            )

        # Update study chapter count
        await self.study_repo.update_chapter_count(study_id)

    async def _get_workspace_id_for_study(self, study_id: str) -> str | None:
        """Get workspace ID for a study."""
        node = await self.node_repo.get_by_id(study_id)
        if node:
            return self._get_workspace_id(node.path)
        return None

    def _get_workspace_id(self, path: str) -> str | None:
        """Extract workspace ID from node path."""
        parts = path.strip("/").split("/")
        if parts:
            return parts[0]
        return None

    def _header_value(self, game: PGNGame, key: str, default: str) -> str:
        """Resolve a PGN header value with a fallback."""
        return game.headers.get(key, default)
