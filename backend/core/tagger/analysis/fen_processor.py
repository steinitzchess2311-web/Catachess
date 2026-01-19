"""
FEN Index Processor for tagger analysis.

Processes fen_index.json files and extracts node-level FEN data
for tagging analysis.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NodeFenEntry:
    """A single node's FEN data for analysis."""
    node_id: str
    fen: str
    uci: Optional[str] = None
    san: Optional[str] = None


class FenIndexProcessor:
    """
    Processes fen_index.json files for node-level analysis.

    Input: chapters/{chapter_id}.fen_index.json from R2
    Output: List of (node_id, fen) pairs for tagging
    """

    def __init__(self, r2_client: Optional[Any] = None):
        """
        Initialize processor.

        Args:
            r2_client: Optional R2 client for fetching fen_index
        """
        self.r2_client = r2_client

    def process_fen_index(self, fen_index: Dict[str, str]) -> List[NodeFenEntry]:
        """
        Process a fen_index dict and extract node entries.

        Args:
            fen_index: Dict mapping node_id to FEN string

        Returns:
            List of NodeFenEntry objects
        """
        entries = []
        for node_id, fen in fen_index.items():
            # Skip virtual root
            if node_id == "virtual_root":
                continue

            entries.append(NodeFenEntry(
                node_id=node_id,
                fen=fen,
            ))

        logger.debug(f"Processed {len(entries)} FEN entries")
        return entries

    def process_fen_index_file(self, file_path: str | Path) -> List[NodeFenEntry]:
        """
        Load and process a fen_index.json file from disk.

        Args:
            file_path: Path to fen_index.json

        Returns:
            List of NodeFenEntry objects
        """
        path = Path(file_path)
        fen_index = json.loads(path.read_text(encoding="utf-8"))
        return self.process_fen_index(fen_index)

    def process_tree_with_moves(self, tree_dict: Dict[str, Any]) -> List[NodeFenEntry]:
        """
        Process a tree_json dict and extract nodes with FEN and moves.

        This provides more complete data including UCI moves for analysis.

        Args:
            tree_dict: Dict from chapters/{chapter_id}.tree.json

        Returns:
            List of NodeFenEntry objects with moves
        """
        entries = []
        nodes = tree_dict.get("nodes", {})

        for node_id, node_data in nodes.items():
            # Skip virtual root
            if node_id == "virtual_root" or node_data.get("san") == "<root>":
                continue

            entries.append(NodeFenEntry(
                node_id=node_id,
                fen=node_data.get("fen", ""),
                uci=node_data.get("uci"),
                san=node_data.get("san"),
            ))

        logger.debug(f"Processed {len(entries)} tree nodes")
        return entries

    async def load_and_process(self, chapter_id: str) -> List[NodeFenEntry]:
        """
        Load fen_index from R2 and process it.

        Args:
            chapter_id: Chapter ID to load

        Returns:
            List of NodeFenEntry objects

        Raises:
            ValueError: If R2 client not configured
        """
        if not self.r2_client:
            raise ValueError("R2 client not configured")

        from modules.workspace.storage.keys import R2Keys

        # Try fen_index first, fall back to tree_json
        try:
            key = R2Keys.chapter_fen_index_json(chapter_id)
            json_str = self.r2_client.download_json(key)
            fen_index = json.loads(json_str)
            return self.process_fen_index(fen_index)
        except Exception as e:
            logger.warning(f"Failed to load fen_index for {chapter_id}: {e}")

            # Fall back to tree_json
            key = R2Keys.chapter_tree_json(chapter_id)
            json_str = self.r2_client.download_json(key)
            tree_dict = json.loads(json_str)
            return self.process_tree_with_moves(tree_dict)


def process_fen_index_json(fen_index_json: str) -> List[NodeFenEntry]:
    """
    Convenience function to process a JSON string.

    Args:
        fen_index_json: JSON string of fen_index

    Returns:
        List of NodeFenEntry objects
    """
    fen_index = json.loads(fen_index_json)
    processor = FenIndexProcessor()
    return processor.process_fen_index(fen_index)
