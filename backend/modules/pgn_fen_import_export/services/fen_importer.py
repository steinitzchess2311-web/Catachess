"""
FEN Importer Service

Business logic for creating Study Chapters from FEN positions.
"""

import json
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from modules.workspace.db.tables.studies import Chapter
from modules.workspace.storage.keys import R2Keys
from modules.workspace.storage.r2_client import R2Client

from .fen_validator import validate_fen, is_standard_fen


def create_empty_tree() -> Dict[str, Any]:
    """
    Create an empty tree.json structure.

    Returns:
        Empty tree with only root node

    Example:
        {
            "version": "v1",
            "rootId": "root",
            "nodes": {
                "root": {
                    "id": "root",
                    "san": null,
                    "uci": null,
                    "fen": null,
                    "children": [],
                    "comment": null,
                    "nags": []
                }
            },
            "meta": {
                "result": null
            }
        }
    """
    root_id = "root"
    return {
        "version": "v1",
        "rootId": root_id,
        "nodes": {
            root_id: {
                "id": root_id,
                "san": None,
                "uci": None,
                "fen": None,
                "children": [],
                "comment": None,
                "nags": [],
            }
        },
        "meta": {
            "result": None
        }
    }


def create_chapter_from_fen(
    study_id: str,
    chapter_title: str,
    fen: str,
    order: int = 0
) -> Chapter:
    """
    Create a Chapter model from FEN position.

    Args:
        study_id: Parent study ID
        chapter_title: Title for the chapter
        fen: FEN string for starting position
        order: Chapter order (default: 0)

    Returns:
        Chapter model ready to be saved

    Raises:
        ValueError: If FEN validation fails
    """
    # Validate FEN
    validation = validate_fen(fen)
    if not validation.valid:
        raise ValueError(f"Invalid FEN: {validation.error}")

    # Use normalized FEN (with all 6 parts)
    normalized_fen = validation.normalized_fen

    # Generate chapter ID
    chapter_id = str(uuid4())

    # Determine starting_fen value
    # NULL = standard position (save space)
    # Non-NULL = custom position
    starting_fen_value = None if is_standard_fen(normalized_fen) else normalized_fen

    # Create Chapter model
    chapter = Chapter(
        id=chapter_id,
        study_id=study_id,
        title=chapter_title,
        order=order,
        white=None,
        black=None,
        event=None,
        date=None,
        result=None,
        r2_key=R2Keys.chapter_tree_json(chapter_id),
        starting_fen=starting_fen_value,  # ✅ New field
        pgn_hash=None,
        pgn_size=None,
        pgn_status=None,
        r2_etag=None,
        last_synced_at=None,
    )

    return chapter


