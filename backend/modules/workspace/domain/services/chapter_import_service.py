"""
Chapter import service.

Handles PGN import, chapter detection, auto-splitting, and R2 storage.
"""

import asyncio
import logging
from datetime import datetime, timezone
from ulid import ULID
from fastapi import BackgroundTasks

from modules.workspace.db.repos.node_repo import NodeRepository
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.repos.variation_repo import VariationRepository
from modules.workspace.db.tables.nodes import Node as NodeTable
from modules.workspace.db.tables.studies import Chapter as ChapterTable
from modules.workspace.db.tables.studies import Study as StudyTable
from modules.workspace.db.tables.variations import Variation, MoveAnnotation
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
from modules.workspace.db.session import get_db_config

# New v2 imports
from backend.core.real_pgn.parser import parse_pgn
from backend.core.real_pgn.builder import build_pgn
from backend.core.real_pgn.fen import build_fen_index
from modules.workspace.pgn_v2.adapters import tree_to_db_changes
from modules.workspace.pgn_v2.repo import PgnV2Repo
from backend.core.tagger.analysis.pipeline import AnalysisPipeline

logger = logging.getLogger(__name__)


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
        variation_repo: VariationRepository,
        r2_client: R2Client,
        event_bus: EventBus,
    ):
        """
        Initialize service.

        Args:
            node_service: Node service for node operations
            node_repo: Node repository
            study_repo: Study repository
            variation_repo: Variation repository for move storage
            r2_client: R2 storage client
            event_bus: Event bus for publishing
        """
        self.node_service = node_service
        self.node_repo = node_repo
        self.study_repo = study_repo
        self.variation_repo = variation_repo
        self.r2_client = r2_client
        self.event_bus = event_bus
        self.pgn_v2_repo = PgnV2Repo(r2_client)
        # Initialize AnalysisPipeline with PgnV2Repo
        self.analysis_pipeline = AnalysisPipeline(
            pgn_path="", # Dummy path, not used for fen_index analysis
            output_dir="/tmp", # Dummy output dir, not used for R2 save
            pgn_v2_repo=self.pgn_v2_repo,
        )

    async def import_pgn(
        self, command: ImportPGNCommand, actor_id: str, background_tasks: BackgroundTasks
    ) -> ImportResult:
        """
        Import PGN content, creating studies and chapters.
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
                command, all_games, actor_id, background_tasks
            )
        else:
            # Multi-study workflow (split)
            if not command.auto_split:
                raise ChapterImportError(
                    f"PGN has {detection.total_chapters} chapters (> 64). "
                    "Enable auto_split to create multiple studies."
                )

            return await self._import_multi_study(
                command, all_games, detection, actor_id, background_tasks
            )

    async def import_pgn_into_study(
        self, study_id: str, pgn_content: str, actor_id: str, background_tasks: BackgroundTasks
    ) -> ImportResult:
        """
        Import PGN content into an existing study as new chapters.
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
            return await self._import_multi_study(command, games, detection, actor_id, background_tasks)

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

        await self._add_chapters_to_study(study_id, games, actor_id, background_tasks)
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
        background_tasks: BackgroundTasks,
    ) -> ImportResult:
        """
        Import PGN into single study.
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
        await self._add_chapters_to_study(study.id, games, actor_id, background_tasks)

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
        background_tasks: BackgroundTasks,
    ) -> ImportResult:
        """
        Import PGN into multiple studies (split workflow).
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
            await self._add_chapters_to_study(study.id, games, actor_id, background_tasks)

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
        self, study_id: str, games: list[PGNGame], actor_id: str, background_tasks: BackgroundTasks
    ) -> None:
        """
        Add chapters to study.
        This is the fast part: only writes to DB. Slow I/O is in background.
        """
        for i, game in enumerate(games):
            chapter_id = str(ULID())
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
                r2_key=R2Keys.chapter_pgn(chapter_id),
                pgn_hash=None,
                pgn_size=None,
                pgn_status="processing", # Set initial status
                r2_etag=None,
                last_synced_at=None,
            )
            await self.study_repo.create_chapter(chapter)

            try:
                tree = parse_pgn(game.raw)
                tree.meta.headers["ChapterId"] = chapter_id
                changes = tree_to_db_changes(
                    tree=tree,
                    current_variations=[],
                    current_annotations=[],
                    VariationCls=Variation,
                    MoveAnnotationCls=MoveAnnotation,
                    actor_id=actor_id,
                )
                
                added_variations = changes["added_variations"]
                added_annotations = changes["added_annotations"]

                if added_variations:
                    deferred_next_ids = {}
                    for var in added_variations:
                        if var.parent_id == "virtual_root":
                            var.parent_id = None
                        deferred_next_ids[var.id] = var.next_id
                        var.next_id = None
                    
                    await self.variation_repo.create_variations_bulk(added_variations)
                    
                    # Bulk update next_id once all rows exist
                    await self.variation_repo.update_variation_next_ids_bulk(deferred_next_ids)

                if added_annotations:
                    await self.variation_repo.create_annotations_bulk(added_annotations)

                # Dispatch slow I/O tasks to the background
                background_tasks.add_task(
                    self._schedule_post_import_processing,
                    chapter_id=chapter_id,
                    study_id=study_id,
                    actor_id=actor_id,
                    game_raw=game.raw,
                    order=i,
                )
            except Exception as e:
                logger.error(f"Failed to process chapter {chapter_id} for DB insertion: {e}")
                chapter.pgn_status = "error"
                await self.study_repo.update_chapter(chapter)
                background_tasks.add_task(
                    self._schedule_post_import_raw,
                    chapter_id=chapter_id,
                    study_id=study_id,
                    actor_id=actor_id,
                    game_raw=game.raw,
                    order=i,
                )


        # Update study chapter count immediately
        await self.study_repo.update_chapter_count(study_id)

    def _schedule_post_import_processing(
        self,
        chapter_id: str,
        study_id: str,
        actor_id: str,
        game_raw: str,
        order: int,
    ) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                self._post_import_processing(
                    chapter_id=chapter_id,
                    study_id=study_id,
                    actor_id=actor_id,
                    game_raw=game_raw,
                    order=order,
                )
            )
        except RuntimeError:
            asyncio.run(
                self._post_import_processing(
                    chapter_id=chapter_id,
                    study_id=study_id,
                    actor_id=actor_id,
                    game_raw=game_raw,
                    order=order,
                )
            )

    def _schedule_post_import_raw(
        self,
        chapter_id: str,
        study_id: str,
        actor_id: str,
        game_raw: str,
        order: int,
    ) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                self._post_import_raw_pgn(
                    chapter_id=chapter_id,
                    study_id=study_id,
                    actor_id=actor_id,
                    game_raw=game_raw,
                    order=order,
                )
            )
        except RuntimeError:
            asyncio.run(
                self._post_import_raw_pgn(
                    chapter_id=chapter_id,
                    study_id=study_id,
                    actor_id=actor_id,
                    game_raw=game_raw,
                    order=order,
                )
            )

    async def _post_import_processing(self, chapter_id: str, study_id: str, actor_id: str, game_raw: str, order: int):
        """
        Handles slow I/O operations for a chapter import in the background.
        """
        try:
            logger.info(f"Starting post-import processing for chapter {chapter_id}")
            try:
                tree = parse_pgn(game_raw)
                tree.meta.headers["ChapterId"] = chapter_id
            except Exception as parse_exc:
                logger.error(f"Post-import parse failed for chapter {chapter_id}: {parse_exc}")
                await self._post_import_raw_pgn(
                    chapter_id=chapter_id,
                    study_id=study_id,
                    actor_id=actor_id,
                    game_raw=game_raw,
                    order=order,
                )
                return

            # Build PGN and FEN index for R2
            pgn_text = build_pgn(tree)
            fen_index = build_fen_index(tree)

            # Upload all artifacts to R2
            upload_result = self.pgn_v2_repo.save_snapshot_pgn(
                chapter_id=chapter_id,
                pgn_text=pgn_text,
                metadata={
                    "study_id": study_id,
                    "chapter_id": chapter_id,
                    "order": str(order),
                },
            )

            self.pgn_v2_repo.save_tree_json(
                chapter_id=chapter_id,
                tree=tree,
                metadata={"chapter_id": chapter_id},
            )

            self.pgn_v2_repo.save_fen_index(
                chapter_id=chapter_id,
                fen_index=fen_index,
                metadata={"chapter_id": chapter_id},
            )

            # Run tagger analysis and save tags to R2
            try:
                tree_data = self.pgn_v2_repo._tree_to_dict(tree)
                await self.analysis_pipeline.run_fen_index_and_save(
                    fen_index=fen_index,
                    chapter_id=chapter_id,
                    tree_data=tree_data,
                    verbose=False,
                )
                logger.info(f"Tagger analysis completed for chapter {chapter_id}")
            except Exception as tagger_e:
                logger.error(f"Tagger analysis failed for chapter {chapter_id}: {tagger_e}")

            # Final chapter update with R2 metadata
            config = get_db_config()
            async with config.async_session_maker() as session:
                study_repo = StudyRepository(session)
                node_repo = NodeRepository(session)
                event_bus = EventBus(session)
                chapter = await study_repo.get_chapter_by_id(chapter_id)
                if chapter:
                    chapter.pgn_hash = upload_result.content_hash
                    chapter.pgn_size = upload_result.size
                    chapter.pgn_status = "ready"
                    chapter.r2_etag = upload_result.etag
                    chapter.last_synced_at = datetime.now(timezone.utc)
                    await study_repo.update_chapter(chapter)
                    await session.commit()
                    logger.info(f"Finished post-import processing for chapter {chapter_id}")

                    # Publish event now that chapter is fully processed
                    await publish_chapter_imported(
                        event_bus,
                        actor_id=actor_id,
                        study_id=study_id,
                        chapter_id=chapter_id,
                        title=chapter.title,
                        order=order,
                        r2_key=chapter.r2_key,
                        workspace_id=await self._get_workspace_id_for_study_with_repo(node_repo, study_id),
                    )

        except Exception as e:
            logger.error(f"Post-import processing failed for chapter {chapter_id}: {e}", exc_info=True)
            config = get_db_config()
            async with config.async_session_maker() as session:
                study_repo = StudyRepository(session)
                chapter = await study_repo.get_chapter_by_id(chapter_id)
                if chapter:
                    chapter.pgn_status = "error"
                    await study_repo.update_chapter(chapter)
                    await session.commit()

    async def _post_import_raw_pgn(
        self,
        chapter_id: str,
        study_id: str,
        actor_id: str,
        game_raw: str,
        order: int,
    ) -> None:
        logger.info(f"Uploading raw PGN for chapter {chapter_id} after parse failure.")
        try:
            upload_result = self.r2_client.upload_pgn(
                key=R2Keys.chapter_pgn(chapter_id),
                content=game_raw,
                metadata={
                    "study_id": study_id,
                    "chapter_id": chapter_id,
                    "order": str(order),
                },
            )
            config = get_db_config()
            async with config.async_session_maker() as session:
                study_repo = StudyRepository(session)
                chapter = await study_repo.get_chapter_by_id(chapter_id)
                if chapter:
                    chapter.pgn_hash = upload_result.content_hash
                    chapter.pgn_size = upload_result.size
                    chapter.pgn_status = "error"
                    chapter.r2_etag = upload_result.etag
                    chapter.last_synced_at = datetime.now(timezone.utc)
                    await study_repo.update_chapter(chapter)
                    await session.commit()
        except Exception as raw_exc:
            logger.error(f"Raw PGN upload failed for chapter {chapter_id}: {raw_exc}")

    async def _get_workspace_id_for_study(self, study_id: str) -> str | None:
        """Get workspace ID for a study."""
        node = await self.node_repo.get_by_id(study_id)
        if node:
            return self._get_workspace_id(node.path)
        return None

    async def _get_workspace_id_for_study_with_repo(
        self, node_repo: NodeRepository, study_id: str
    ) -> str | None:
        """Get workspace ID for a study using a specific repository."""
        node = await node_repo.get_by_id(study_id)
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
