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
from backend.core.config import settings # New import

logger = logging.getLogger(__name__)

PGN_STATUS_READY = "ready"
PGN_STATUS_ERROR = "error"


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

        If PGN V2 is disabled, skips sync.

        Returns the PGN string, or None if the chapter has no moves.
        """
        if not settings.PGN_V2_ENABLED:
            logger.warning(f"PGN V2 is disabled. Skipping PGN sync for chapter {chapter_id}")
            return None

        chapter = await self.study_repo.get_chapter_by_id(chapter_id)
        if not chapter:
            return None

        try:
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
                logger.info(f"Chapter {chapter_id} is empty. Preserving r2_key and marking as ready.")
                # IMPORTANT: Preserve r2_key to maintain chapter_id ↔ r2_key alignment
                # r2_key is NOT NULL in DB, so we must keep it (or set standard key if missing)
                if not chapter.r2_key:
                    chapter.r2_key = R2Keys.chapter_pgn(chapter_id)
                # Clear metadata but keep r2_key for consistency
                chapter.pgn_hash = None
                chapter.pgn_size = 0
                chapter.r2_etag = None
                chapter.last_synced_at = datetime.now(timezone.utc)
                chapter.pgn_status = PGN_STATUS_READY
                await self.study_repo.update_chapter(chapter)
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

            # Build PGN using new v2 builder (ONLY for hash/size calculation if needed, or skip)
            # Stage 10: We stop writing PGN to R2 in the sync loop.
            # But we might still want to know the size/hash of the tree?
            # Let's keep PGN generation in memory if we need it for legacy metadata, 
            # OR better: The metadata now tracks the TREE JSON.
            
            # However, `chapter.pgn_hash` and `pgn_size` are named "pgn_...". 
            # We should reuse them for the Tree JSON or leave them null?
            # The prompt says: "Postgres 不变，不新增 tree 字段。" (Postgres unchanged, no new tree fields).
            # So we should probably store tree.json hash/size in pgn_hash/pgn_size columns as a proxy, 
            # OR just accept they refer to the tree now.

            # Upload artifacts to R2
            r2_key = chapter.r2_key or R2Keys.chapter_tree_json(chapter_id) # Prefer tree key? 
            # Wait, checklist says: "R2 key 必须使用 R2Keys.chapter_tree_json(chapter_id)"
            # So chapter.r2_key should update to the tree json key?
            # Or R2Keys.chapter_tree_json is derived?
            # keys.py defines `chapter_tree_json` as separate key.
            # `chapter.r2_key` in DB is traditionally the PGN key.
            # If we change `chapter.r2_key` to point to `.tree.json`, it changes semantics.
            # "chapter_id 对齐 key，不允许新路径格式" -> means strictly `chapters/{chapter_id}.tree.json`.
            
            # Let's see:
            # 1. Upload tree JSON
            tree_upload = self.pgn_v2_repo.save_tree_json(
                chapter_id=chapter_id,
                tree=tree,
                metadata={"chapter_id": chapter_id},
            )

            # 2. Skip FEN index persistence (Stage 12: tree.json only)
            # 3. Skip PGN upload (Export only)

            # Update chapter metadata
            # We map pgn_hash/size to the TREE JSON artifact for now, as that's the primary artifact.
            chapter.r2_key = R2Keys.chapter_tree_json(chapter_id)
            chapter.pgn_hash = tree_upload.content_hash
            chapter.pgn_size = tree_upload.size
            chapter.r2_etag = tree_upload.etag
            chapter.last_synced_at = datetime.now(timezone.utc)
            chapter.pgn_status = PGN_STATUS_READY
            await self.study_repo.update_chapter(chapter)

            logger.info(
                "PGN sync ready (Tree JSON)",
                extra={
                    "study_id": chapter.study_id,
                    "chapter_id": chapter_id,
                    "r2_key": chapter.r2_key,
                    "error_code": None,
                },
            )
            return None # No PGN text returned implies we didn't generate/upload it.
        except Exception:
            chapter.pgn_status = PGN_STATUS_ERROR
            await self.study_repo.update_chapter(chapter)
            logger.error(
                "PGN sync failed",
                exc_info=True,
                extra={
                    "study_id": chapter.study_id,
                    "chapter_id": chapter_id,
                    "r2_key": chapter.r2_key,
                    "error_code": "pgn_sync_failed",
                },
            )
            raise

    async def sync_chapter_pgn_legacy(self, chapter_id: str) -> str | None:
        """
        Legacy sync method using old serializer (for comparison/fallback).

        Returns the PGN string, or None if the chapter has no moves.
        """
        chapter = await self.study_repo.get_chapter_by_id(chapter_id)
        if not chapter:
            return None

        try:
            variations = await self.variation_repo.get_variations_for_chapter(chapter_id)
            annotations = await self.variation_repo.get_annotations_for_chapter(chapter_id)
            root = variations_to_tree(variations, annotations)
            if root is None:
                logger.info(f"Chapter {chapter_id} is empty (legacy). Preserving r2_key and marking as ready.")
                # IMPORTANT: Preserve r2_key to maintain chapter_id ↔ r2_key alignment
                # r2_key is NOT NULL in DB, so we must keep it (or set standard key if missing)
                if not chapter.r2_key:
                    chapter.r2_key = R2Keys.chapter_pgn(chapter_id)
                # Clear metadata but keep r2_key for consistency
                chapter.pgn_hash = None
                chapter.pgn_size = 0
                chapter.r2_etag = None
                chapter.last_synced_at = datetime.now(timezone.utc)
                chapter.pgn_status = PGN_STATUS_READY
                await self.study_repo.update_chapter(chapter)
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
            chapter.pgn_status = PGN_STATUS_READY
            await self.study_repo.update_chapter(chapter)

            logger.info(
                "PGN sync ready (legacy)",
                extra={
                    "study_id": chapter.study_id,
                    "chapter_id": chapter_id,
                    "r2_key": r2_key,
                    "error_code": None,
                },
            )
            return pgn_text
        except Exception:
            chapter.pgn_status = PGN_STATUS_ERROR
            await self.study_repo.update_chapter(chapter)
            logger.error(
                "PGN sync failed (legacy)",
                exc_info=True,
                extra={
                    "study_id": chapter.study_id,
                    "chapter_id": chapter_id,
                    "r2_key": chapter.r2_key,
                    "error_code": "pgn_sync_failed_legacy",
                },
            )
            raise
