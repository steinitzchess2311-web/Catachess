"""
Sync chapter PGN to R2 after move/annotation edits.
"""

import logging
from datetime import datetime, timezone

from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.repos.variation_repo import VariationRepository
from modules.workspace.db.tables.variations import Variation, MoveAnnotation
from modules.workspace.pgn.serializer.from_variations import variations_to_tree
from modules.workspace.pgn.serializer.to_pgn import tree_to_pgn
from modules.workspace.storage.keys import R2Keys
from modules.workspace.storage.r2_client import R2Client

# New v2 imports
from modules.workspace.pgn_v2.adapters import db_to_tree
from modules.workspace.pgn_v2.repo import PgnV2Repo, validate_chapter_r2_key, backfill_chapter_r2_key
from backend.core.real_pgn.builder import build_pgn
from backend.core.real_pgn.fen import build_fen_index
from backend.core.config import settings # New import

logger = logging.getLogger(__name__)


class PgnSyncService:
    """
    Build PGN from variation rows and upload to R2.

    This keeps chapter PGN consistent with the move tree in Postgres.
    """

    def __init__(
        self,
        study_repo: StudyRepository,
        variation_repo: VariationRepository,
        r2_client: R2Client,
    ) -> None:
        self.study_repo = study_repo
        self.variation_repo = variation_repo
        self.r2_client = r2_client
        self.pgn_v2_repo = PgnV2Repo(r2_client)

    async def sync_chapter_pgn(self, chapter_id: str) -> str | None:
        """
        Rebuild PGN for a chapter and upload to R2.

        If PGN V2 is disabled, falls back to legacy sync.

        Returns the PGN string, or None if the chapter has no moves.
        """
        if not settings.PGN_V2_ENABLED:
            logger.info(f"PGN V2 is disabled. Using legacy sync for chapter {chapter_id}")
            return await self.sync_chapter_pgn_legacy(chapter_id)

        chapter = await self.study_repo.get_chapter_by_id(chapter_id)
        if not chapter:
            return None

        # B1: Validate and backfill r2_key if needed
        if not validate_chapter_r2_key(chapter):
            standard_key = backfill_chapter_r2_key(chapter)
            chapter.r2_key = standard_key
            await self.study_repo.update_chapter(chapter)

        variations = await self.variation_repo.get_variations_for_chapter(chapter_id)
        annotations = await self.variation_repo.get_annotations_for_chapter(chapter_id)

        # Use new v2 adapter to build NodeTree
        tree = db_to_tree(
            variations=variations,
            annotations=annotations,
            VariationCls=Variation,
            MoveAnnotationCls=MoveAnnotation,
            chapter=chapter,
        )

        if tree.root_id is None or len(tree.nodes) <= 1:  # Only virtual_root
            return None

        # Populate headers from chapter metadata
        tree.meta.headers["Event"] = chapter.title
        tree.meta.headers["Site"] = "CataChess"
        tree.meta.headers["Date"] = chapter.date or datetime.now(timezone.utc).strftime("%Y.%m.%d")
        tree.meta.headers["Round"] = "?"
        tree.meta.headers["White"] = chapter.white or "?"
        tree.meta.headers["Black"] = chapter.black or "?"
        tree.meta.headers["Result"] = chapter.result or "*"
        tree.meta.result = chapter.result or "*"

        # Build PGN using new v2 builder
        pgn_text = build_pgn(tree)

        # Build FEN index
        fen_index = build_fen_index(tree)

        # Upload all artifacts to R2
        r2_key = chapter.r2_key or R2Keys.chapter_pgn(chapter_id)

        # 1. Upload PGN
        upload = self.pgn_v2_repo.save_snapshot_pgn(
            chapter_id=chapter_id,
            pgn_text=pgn_text,
            metadata={"chapter_id": chapter_id},
        )

        # 2. Upload tree JSON
        self.pgn_v2_repo.save_tree_json(
            chapter_id=chapter_id,
            tree=tree,
            metadata={"chapter_id": chapter_id},
        )

        # 3. Upload FEN index
        self.pgn_v2_repo.save_fen_index(
            chapter_id=chapter_id,
            fen_index=fen_index,
            metadata={"chapter_id": chapter_id},
        )

        # Update chapter metadata
        chapter.r2_key = r2_key
        chapter.pgn_hash = upload.content_hash
        chapter.pgn_size = upload.size
        chapter.r2_etag = upload.etag
        chapter.last_synced_at = datetime.now(timezone.utc)
        await self.study_repo.update_chapter(chapter)

        logger.info(f"Synced chapter {chapter_id}: PGN + tree + fen_index")
        return pgn_text

    async def sync_chapter_pgn_legacy(self, chapter_id: str) -> str | None:
        """
        Legacy sync method using old serializer (for comparison/fallback).

        Returns the PGN string, or None if the chapter has no moves.
        """
        chapter = await self.study_repo.get_chapter_by_id(chapter_id)
        if not chapter:
            return None

        variations = await self.variation_repo.get_variations_for_chapter(chapter_id)
        annotations = await self.variation_repo.get_annotations_for_chapter(chapter_id)
        root = variations_to_tree(variations, annotations)
        if root is None:
            return None

        headers = {
            "Event": chapter.title,
            "Site": "CataChess",
            "Date": (chapter.date or datetime.now(timezone.utc).strftime("%Y.%m.%d")),
            "Round": "?",
            "White": chapter.white or "?",
            "Black": chapter.black or "?",
            "Result": chapter.result or "*",
        }
        pgn_text = tree_to_pgn(root, headers=headers, result=chapter.result or "*")

        r2_key = chapter.r2_key or R2Keys.chapter_pgn(chapter_id)
        upload = self.r2_client.upload_pgn(
            key=r2_key,
            content=pgn_text,
            metadata={"chapter_id": chapter_id},
        )

        chapter.r2_key = r2_key
        chapter.pgn_hash = upload.content_hash
        chapter.pgn_size = upload.size
        chapter.r2_etag = upload.etag
        chapter.last_synced_at = datetime.now(timezone.utc)
        await self.study_repo.update_chapter(chapter)

        return pgn_text

    async def sync_chapter_pgn_legacy(self, chapter_id: str) -> str | None:
        """
        Legacy sync method using old serializer (for comparison/fallback).

        Returns the PGN string, or None if the chapter has no moves.
        """
        chapter = await self.study_repo.get_chapter_by_id(chapter_id)
        if not chapter:
            return None

        variations = await self.variation_repo.get_variations_for_chapter(chapter_id)
        annotations = await self.variation_repo.get_annotations_for_chapter(chapter_id)
        root = variations_to_tree(variations, annotations)
        if root is None:
            return None

        headers = {
            "Event": chapter.title,
            "Site": "CataChess",
            "Date": (chapter.date or datetime.now(timezone.utc).strftime("%Y.%m.%d")),
            "Round": "?",
            "White": chapter.white or "?",
            "Black": chapter.black or "?",
            "Result": chapter.result or "*",
        }
        pgn_text = tree_to_pgn(root, headers=headers, result=chapter.result or "*")

        r2_key = chapter.r2_key or R2Keys.chapter_pgn(chapter_id)
        upload = self.r2_client.upload_pgn(
            key=r2_key,
            content=pgn_text,
            metadata={"chapter_id": chapter_id},
        )

        chapter.r2_key = r2_key
        chapter.pgn_hash = upload.content_hash
        chapter.pgn_size = upload.size
        chapter.r2_etag = upload.etag
        chapter.last_synced_at = datetime.now(timezone.utc)
        await self.study_repo.update_chapter(chapter)

        return pgn_text
