"""
R2 Repository for PGN v2 artifacts.

Handles storage of:
- Snapshot PGN files
- NodeTree JSON
- FEN index JSON
"""

import json
import logging
from dataclasses import asdict
from typing import Any, Dict, Optional

from backend.modules.workspace.storage.keys import R2Keys, R2Config as KeysConfig
from backend.modules.workspace.storage.r2_client import R2Client, UploadResult
from backend.core.real_pgn.models import NodeTree

logger = logging.getLogger(__name__)


class PgnV2Repo:
    """
    Repository for PGN v2 artifacts in R2.

    Provides methods to save and retrieve:
    - PGN text snapshots
    - NodeTree JSON
    - FEN index JSON
    """

    def __init__(self, r2_client: R2Client):
        """
        Initialize repository with R2 client.

        Args:
            r2_client: Configured R2Client instance
        """
        self.r2_client = r2_client

    def save_snapshot_pgn(
        self,
        chapter_id: str,
        pgn_text: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """
        Save PGN text snapshot to R2.

        Args:
            chapter_id: Chapter identifier
            pgn_text: PGN content as string
            metadata: Optional metadata dict

        Returns:
            UploadResult with upload details
        """
        key = R2Keys.chapter_pgn(chapter_id)
        logger.debug(f"Saving PGN snapshot to {key}")

        result = self.r2_client.upload_pgn(
            key=key,
            content=pgn_text,
            content_type=KeysConfig.CONTENT_TYPE_PGN,
            metadata=metadata,
        )

        logger.info(f"Saved PGN snapshot: {key} ({result.size} bytes)")
        return result

    def save_tree_json(
        self,
        chapter_id: str,
        tree: NodeTree,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """
        Save NodeTree as JSON to R2.

        Args:
            chapter_id: Chapter identifier
            tree: NodeTree to serialize
            metadata: Optional metadata dict

        Returns:
            UploadResult with upload details
        """
        key = R2Keys.chapter_tree_json(chapter_id)
        logger.debug(f"Saving tree JSON to {key}")

        # Serialize NodeTree to JSON
        tree_dict = self._tree_to_dict(tree)
        tree_json = json.dumps(tree_dict, ensure_ascii=False, indent=2)

        result = self.r2_client.upload_json(
            key=key,
            content=tree_json,
            metadata=metadata,
        )

        logger.info(f"Saved tree JSON: {key} ({result.size} bytes)")
        return result

    def save_fen_index(
        self,
        chapter_id: str,
        fen_index: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """
        Save FEN index as JSON to R2.

        Args:
            chapter_id: Chapter identifier
            fen_index: FEN index dict (node_id -> fen mapping or similar)
            metadata: Optional metadata dict

        Returns:
            UploadResult with upload details
        """
        key = R2Keys.chapter_fen_index_json(chapter_id)
        logger.debug(f"Saving FEN index to {key}")

        fen_json = json.dumps(fen_index, ensure_ascii=False, indent=2)

        result = self.r2_client.upload_json(
            key=key,
            content=fen_json,
            metadata=metadata,
        )

        logger.info(f"Saved FEN index: {key} ({result.size} bytes)")
        return result

    def load_snapshot_pgn(self, chapter_id: str) -> str:
        """
        Load PGN text snapshot from R2.

        Args:
            chapter_id: Chapter identifier

        Returns:
            PGN content as string

        Raises:
            ClientError: If download fails
        """
        key = R2Keys.chapter_pgn(chapter_id)
        return self.r2_client.download_pgn(key)

    def load_tree_json(self, chapter_id: str) -> Dict[str, Any]:
        """
        Load NodeTree JSON from R2.

        Args:
            chapter_id: Chapter identifier

        Returns:
            NodeTree as dict

        Raises:
            ClientError: If download fails
        """
        key = R2Keys.chapter_tree_json(chapter_id)
        json_str = self.r2_client.download_json(key)
        return json.loads(json_str)

    def load_fen_index(self, chapter_id: str) -> Dict[str, Any]:
        """
        Load FEN index JSON from R2.

        Args:
            chapter_id: Chapter identifier

        Returns:
            FEN index as dict

        Raises:
            ClientError: If download fails
        """
        key = R2Keys.chapter_fen_index_json(chapter_id)
        json_str = self.r2_client.download_json(key)
        return json.loads(json_str)

    def exists_pgn(self, chapter_id: str) -> bool:
        """Check if PGN snapshot exists."""
        key = R2Keys.chapter_pgn(chapter_id)
        return self.r2_client.exists(key)

    def exists_tree_json(self, chapter_id: str) -> bool:
        """Check if tree JSON exists."""
        key = R2Keys.chapter_tree_json(chapter_id)
        return self.r2_client.exists(key)

    def exists_fen_index(self, chapter_id: str) -> bool:
        """Check if FEN index exists."""
        key = R2Keys.chapter_fen_index_json(chapter_id)
        return self.r2_client.exists(key)

    def save_tags_json(
        self,
        chapter_id: str,
        tags_data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """
        Save tags JSON to R2 (tagger output).

        Args:
            chapter_id: Chapter identifier
            tags_data: Tags data dict (node_id -> tags mapping)
            metadata: Optional metadata dict

        Returns:
            UploadResult with upload details
        """
        key = R2Keys.chapter_tags_json(chapter_id)
        logger.debug(f"Saving tags JSON to {key}")

        tags_json = json.dumps(tags_data, ensure_ascii=False, indent=2)

        result = self.r2_client.upload_json(
            key=key,
            content=tags_json,
            metadata=metadata,
        )

        logger.info(f"Saved tags JSON: {key} ({result.size} bytes)")
        return result

    def load_tags_json(self, chapter_id: str) -> Dict[str, Any]:
        """
        Load tags JSON from R2.

        Args:
            chapter_id: Chapter identifier

        Returns:
            Tags data as dict

        Raises:
            ClientError: If download fails
        """
        key = R2Keys.chapter_tags_json(chapter_id)
        json_str = self.r2_client.download_json(key)
        return json.loads(json_str)

    def exists_tags_json(self, chapter_id: str) -> bool:
        """Check if tags JSON exists."""
        key = R2Keys.chapter_tags_json(chapter_id)
        return self.r2_client.exists(key)

    def delete_all_artifacts(self, chapter_id: str) -> None:
        """
        Delete all R2 artifacts for a chapter.

        Args:
            chapter_id: Chapter identifier
        """
        keys_to_delete = [
            R2Keys.chapter_pgn(chapter_id),
            R2Keys.chapter_tree_json(chapter_id),
            R2Keys.chapter_fen_index_json(chapter_id),
            R2Keys.chapter_tags_json(chapter_id),
        ]

        for key in keys_to_delete:
            try:
                if self.r2_client.exists(key):
                    self.r2_client.delete(key)
                    logger.debug(f"Deleted {key}")
            except Exception as e:
                logger.warning(f"Failed to delete {key}: {e}")

    def _tree_to_dict(self, tree: NodeTree) -> Dict[str, Any]:
        """
        Convert NodeTree to a JSON-serializable dict.

        Args:
            tree: NodeTree to convert

        Returns:
            Dict representation of NodeTree
        """
        nodes_dict = {}
        for node_id, node in tree.nodes.items():
            nodes_dict[node_id] = {
                "node_id": node.node_id,
                "parent_id": node.parent_id,
                "san": node.san,
                "uci": node.uci,
                "ply": node.ply,
                "move_number": node.move_number,
                "fen": node.fen,
                "comment_before": node.comment_before,
                "comment_after": node.comment_after,
                "nags": node.nags,
                "main_child": node.main_child,
                "variations": node.variations,
            }

        meta_dict = {
            "headers": tree.meta.headers,
            "result": tree.meta.result,
            "setup_fen": tree.meta.setup_fen,
        }

        return {
            "root_id": tree.root_id,
            "nodes": nodes_dict,
            "meta": meta_dict,
        }


def validate_chapter_r2_key(chapter: Any, expected_key: Optional[str] = None) -> bool:
    """
    Validate that chapter.r2_key matches the standard key format.

    Args:
        chapter: Chapter object with id and r2_key attributes
        expected_key: Optional override for expected key (defaults to R2Keys.chapter_pgn)

    Returns:
        True if r2_key matches expected, False otherwise
    """
    if expected_key is None:
        expected_key = R2Keys.chapter_pgn(chapter.id)

    if chapter.r2_key != expected_key:
        logger.warning(
            f"Chapter r2_key mismatch: chapter_id={chapter.id}, "
            f"current_key={chapter.r2_key}, expected_key={expected_key}"
        )
        return False

    return True


def backfill_chapter_r2_key(chapter: Any) -> str:
    """
    Get the standard r2_key for a chapter (for migration/backfill).

    Args:
        chapter: Chapter object with id attribute

    Returns:
        Standard r2_key for the chapter
    """
    standard_key = R2Keys.chapter_pgn(chapter.id)
    logger.info(f"Backfilling r2_key for chapter {chapter.id}: {standard_key}")
    return standard_key
