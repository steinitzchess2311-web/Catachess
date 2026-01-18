"""
Sync chapter PGN to R2 after move/annotation edits.
"""

from datetime import datetime, timezone

from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.repos.variation_repo import VariationRepository
from modules.workspace.pgn.serializer.from_variations import variations_to_tree
from modules.workspace.pgn.serializer.to_pgn import tree_to_pgn
from modules.workspace.storage.keys import R2Keys
from modules.workspace.storage.r2_client import R2Client


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

    async def sync_chapter_pgn(self, chapter_id: str) -> str | None:
        """
        Rebuild PGN for a chapter and upload to R2.

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
