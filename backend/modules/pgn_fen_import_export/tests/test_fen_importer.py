"""
Tests for FEN Importer Service

Tests the business logic for creating chapters from FEN positions.
"""

import pytest

from ..services.fen_importer import (
    create_empty_tree,
    create_chapter_from_fen,
)
from ..services.fen_validator import STANDARD_FEN


class TestCreateEmptyTree:
    """Tests for create_empty_tree function."""

    def test_creates_valid_tree_structure(self):
        """Test that empty tree has correct structure."""
        tree = create_empty_tree()

        assert tree["version"] == "v1"
        assert tree["rootId"] == "root"
        assert "nodes" in tree
        assert "meta" in tree

    def test_root_node_exists(self):
        """Test that root node is created."""
        tree = create_empty_tree()

        assert "root" in tree["nodes"]
        root = tree["nodes"]["root"]

        assert root["id"] == "root"
        assert root["san"] is None
        assert root["uci"] is None
        assert root["fen"] is None
        assert root["children"] == []
        assert root["comment"] is None
        assert root["nags"] == []

    def test_meta_has_result(self):
        """Test that meta has result field."""
        tree = create_empty_tree()

        assert tree["meta"]["result"] is None


class TestCreateChapterFromFen:
    """Tests for create_chapter_from_fen function."""

    def test_creates_chapter_with_custom_fen(self):
        """Test creating chapter from custom FEN position."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        chapter = create_chapter_from_fen(
            study_id="study-123",
            chapter_title="Rook Endgame",
            fen=fen,
            order=0
        )

        assert chapter.study_id == "study-123"
        assert chapter.title == "Rook Endgame"
        assert chapter.order == 0
        assert chapter.starting_fen == fen  # Custom position stored
        assert chapter.id is not None
        assert chapter.r2_key is not None

    def test_creates_chapter_with_standard_fen(self):
        """Test creating chapter from standard position."""
        chapter = create_chapter_from_fen(
            study_id="study-123",
            chapter_title="Standard Opening",
            fen=STANDARD_FEN,
            order=0
        )

        assert chapter.study_id == "study-123"
        assert chapter.title == "Standard Opening"
        assert chapter.starting_fen is None  # ✅ Standard position = NULL

    def test_normalizes_fen_with_4_parts(self):
        """Test that FEN with 4 parts is normalized to 6 parts."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq -"
        chapter = create_chapter_from_fen(
            study_id="study-123",
            chapter_title="Test",
            fen=fen,
            order=0
        )

        # Should be normalized to have 6 parts
        assert chapter.starting_fen == f"{fen} 0 1"

    def test_rejects_invalid_fen(self):
        """Test that invalid FEN raises ValueError."""
        with pytest.raises(ValueError, match="Invalid FEN"):
            create_chapter_from_fen(
                study_id="study-123",
                chapter_title="Test",
                fen="invalid fen string",
                order=0
            )

    def test_generates_unique_chapter_ids(self):
        """Test that multiple chapters get unique IDs."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"

        chapter1 = create_chapter_from_fen(
            study_id="study-123",
            chapter_title="Chapter 1",
            fen=fen,
            order=0
        )

        chapter2 = create_chapter_from_fen(
            study_id="study-123",
            chapter_title="Chapter 2",
            fen=fen,
            order=1
        )

        assert chapter1.id != chapter2.id

    def test_r2_key_follows_convention(self):
        """Test that R2 key follows naming convention."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        chapter = create_chapter_from_fen(
            study_id="study-123",
            chapter_title="Test",
            fen=fen,
            order=0
        )

        # R2 key should be: chapters/{chapter_id}.tree.json
        assert chapter.r2_key.startswith("chapters/")
        assert chapter.r2_key.endswith(".tree.json")
        assert chapter.id in chapter.r2_key

    def test_chapter_has_no_game_metadata(self):
        """Test that FEN-created chapter has no game metadata."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        chapter = create_chapter_from_fen(
            study_id="study-123",
            chapter_title="Test",
            fen=fen,
            order=0
        )

        # FEN imports don't have game metadata
        assert chapter.white is None
        assert chapter.black is None
        assert chapter.event is None
        assert chapter.date is None
        assert chapter.result is None

    def test_chapter_has_no_integrity_info_initially(self):
        """Test that new chapter has no integrity info."""
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        chapter = create_chapter_from_fen(
            study_id="study-123",
            chapter_title="Test",
            fen=fen,
            order=0
        )

        assert chapter.pgn_hash is None
        assert chapter.pgn_size is None
        assert chapter.pgn_status is None
        assert chapter.last_synced_at is None
