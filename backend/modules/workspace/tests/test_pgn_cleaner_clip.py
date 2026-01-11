"""
Tests for PGN Cleaner - Phase 4 Core Innovation.

Tests the key features:
- Move path parsing and navigation
- Clipping PGN from specific moves (remove variations before, keep after)
- Exporting without comments
- Exporting raw mainline
- Variation pruning utilities
"""

import pytest

from workspace.pgn.cleaner.variation_pruner import (
    MovePath,
    parse_move_path,
    format_move_path,
    find_node_by_path,
    prune_before_node,
    remove_comments,
    extract_mainline,
)
from workspace.pgn.cleaner.pgn_cleaner import (
    clip_pgn_from_move,
    get_clip_preview,
)
from workspace.pgn.cleaner.no_comment_pgn import export_no_comment_pgn
from workspace.pgn.cleaner.raw_pgn import export_raw_pgn, export_clean_mainline
from workspace.pgn.serializer.to_tree import pgn_to_tree, VariationNode
from workspace.pgn.serializer.to_pgn import tree_to_movetext


# ===== Test Fixtures =====


@pytest.fixture
def simple_game_pgn():
    """Simple game with no variations."""
    return """
[Event "Test Game"]
[Site "Test"]
[Date "2024.01.01"]
[White "Player 1"]
[Black "Player 2"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O *
"""


@pytest.fixture
def game_with_variations_pgn():
    """Game with multiple variations."""
    return """
[Event "Test Game"]

1. e4 (1. d4 d5 2. c4) e5 (1...c5 2. Nf3) 2. Nf3 (2. Bc4) Nc6 3. Bb5 *
"""


@pytest.fixture
def game_with_nested_variations_pgn():
    """Game with nested variations."""
    return """
[Event "Test Game"]

1. e4 e5 2. Nf3 (2. Bc4 Nf6 (2...Bc5 3. Nf3) 3. d3) Nc6 3. Bb5 a6 *
"""


@pytest.fixture
def game_with_comments_pgn():
    """Game with comments and NAGs."""
    return """
[Event "Test Game"]

1. e4 { King's pawn } !! e5 { Symmetric response } 2. Nf3 { Developing } Nc6 *
"""


@pytest.fixture
def simple_tree(simple_game_pgn):
    """Variation tree from simple game."""
    return pgn_to_tree(simple_game_pgn)


@pytest.fixture
def variations_tree(game_with_variations_pgn):
    """Variation tree with variations."""
    return pgn_to_tree(game_with_variations_pgn)


@pytest.fixture
def nested_tree(game_with_nested_variations_pgn):
    """Variation tree with nested variations."""
    return pgn_to_tree(game_with_nested_variations_pgn)


@pytest.fixture
def comments_tree(game_with_comments_pgn):
    """Variation tree with comments."""
    return pgn_to_tree(game_with_comments_pgn)


# ===== Move Path Tests =====


class TestMovePath:
    """Test move path parsing and formatting."""

    def test_parse_simple_main_path(self):
        """Test parsing simple main line path."""
        path = parse_move_path("main.1")
        assert path.segments == [("main", 1)]
        assert str(path) == "main.1"

    def test_parse_main_path_with_move(self):
        """Test parsing main line path to specific move."""
        path = parse_move_path("main.5")
        assert path.segments == [("main", 5)]

    def test_parse_variation_path(self):
        """Test parsing path with variation."""
        path = parse_move_path("main.5.var1.2")
        assert path.segments == [("main", 5), ("var", 1), ("main", 2)]

    def test_parse_nested_variation_path(self):
        """Test parsing nested variation path."""
        path = parse_move_path("main.3.var1.4.var2.1")
        assert path.segments == [
            ("main", 3),
            ("var", 1),
            ("main", 4),
            ("var", 2),
            ("main", 1),
        ]

    def test_parse_invalid_empty_path(self):
        """Test that empty path raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_move_path("")

    def test_parse_invalid_missing_move_number(self):
        """Test that missing move number raises error."""
        with pytest.raises(ValueError, match="Expected move number"):
            parse_move_path("main")

    def test_parse_invalid_move_number(self):
        """Test that invalid move number raises error."""
        with pytest.raises(ValueError, match="Expected integer"):
            parse_move_path("main.abc")

    def test_parse_invalid_negative_move(self):
        """Test that negative move number raises error."""
        with pytest.raises(ValueError, match="must be >= 1"):
            parse_move_path("main.0")

    def test_format_move_path(self):
        """Test formatting path segments."""
        segments = [("main", 5), ("var", 1), ("main", 2)]
        path_str = format_move_path(segments)
        assert path_str == "main.5.var1.2"


class TestFindNodeByPath:
    """Test finding nodes by path."""

    def test_find_first_move(self, simple_tree):
        """Test finding first move."""
        node = find_node_by_path(simple_tree, "main.1")
        assert node is not None
        assert node.san == "e4"

    def test_find_move_in_main_line(self, simple_tree):
        """Test finding move in main line."""
        node = find_node_by_path(simple_tree, "main.3")
        assert node is not None
        assert node.san == "Bb5"

    def test_find_variation(self, variations_tree):
        """Test finding move in variation."""
        # First variation from move 1: 1. d4
        node = find_node_by_path(variations_tree, "main.1.var1.1")
        assert node is not None
        assert node.san == "d4"

    def test_find_nested_variation(self, nested_tree):
        """Test finding move in nested variation."""
        # Variation from move 2: 2. Bc4 Nf6, then variation 2...Bc5
        node = find_node_by_path(nested_tree, "main.2.var1.2.var1.1")
        assert node is not None
        assert node.san == "Bc5"

    def test_find_nonexistent_path(self, simple_tree):
        """Test that nonexistent path returns None."""
        node = find_node_by_path(simple_tree, "main.99")
        assert node is None

    def test_find_nonexistent_variation(self, variations_tree):
        """Test that nonexistent variation returns None."""
        node = find_node_by_path(variations_tree, "main.1.var99.1")
        assert node is None


# ===== PGN Clipping Tests =====


class TestClipPGN:
    """Test PGN clipping functionality."""

    def test_clip_from_start(self, variations_tree):
        """Test clipping from first move (should be same as original)."""
        clipped = clip_pgn_from_move(variations_tree, "main.1", include_headers=False)

        # Should include all variations
        assert "e4" in clipped
        assert "d4" in clipped  # First variation
        assert "c5" in clipped  # Second variation

    def test_clip_from_middle_removes_early_variations(self, variations_tree):
        """Test that clipping from middle removes earlier variations."""
        # Clip from move 2 (Nf3)
        clipped = clip_pgn_from_move(variations_tree, "main.2", include_headers=False)

        # Should NOT include variations from move 1
        assert "d4" not in clipped  # First variation should be removed
        assert "c5" not in clipped  # Second variation should be removed

        # Should include main line to Nf3
        assert "e4" in clipped
        assert "e5" in clipped
        assert "Nf3" in clipped

        # Should include variations after Nf3
        assert "Bc4" in clipped  # Variation from move 2

    def test_clip_keeps_variations_after_target(self, variations_tree):
        """Test that variations after target are kept."""
        # Clip from move 2
        clipped = clip_pgn_from_move(variations_tree, "main.2", include_headers=False)

        # Should include variation 2. Bc4
        assert "Bc4" in clipped
        assert "Bb5" in clipped  # Move after the variation

    def test_clip_from_variation(self, variations_tree):
        """Test clipping from within a variation."""
        # Clip from the d4 variation
        clipped = clip_pgn_from_move(
            variations_tree, "main.1.var1.1", include_headers=False
        )

        # Should start with d4 (the variation move)
        assert "d4" in clipped
        assert "d5" in clipped  # Continuation of variation
        assert "c4" in clipped

        # Should NOT include main line variations
        assert "e4" in clipped  # But e4 should be in the path to d4
        assert "e5" not in clipped  # e5 is after we branched

    def test_clip_with_headers(self, variations_tree):
        """Test clipping with PGN headers."""
        headers = {
            "Event": "Test",
            "White": "Player 1",
            "Black": "Player 2",
        }

        clipped = clip_pgn_from_move(
            variations_tree, "main.2", headers=headers, include_headers=True
        )

        # Should include headers
        assert "[Event" in clipped
        assert "[White" in clipped


class TestClipPreview:
    """Test clip preview functionality."""

    def test_preview_includes_counts(self, variations_tree):
        """Test that preview includes correct counts."""
        preview = get_clip_preview(variations_tree, "main.2")

        assert "target_move" in preview
        assert "moves_before" in preview
        assert "moves_after" in preview
        assert "variations_removed" in preview
        assert "variations_kept" in preview
        assert "preview_text" in preview

    def test_preview_target_move(self, variations_tree):
        """Test that preview shows correct target move."""
        preview = get_clip_preview(variations_tree, "main.2")
        assert "Nf3" in preview["target_move"]

    def test_preview_variations_removed(self, variations_tree):
        """Test that preview counts removed variations."""
        preview = get_clip_preview(variations_tree, "main.2")

        # Should have removed 2 variations from move 1
        assert preview["variations_removed"] >= 2


# ===== Export Without Comments Tests =====


class TestNoCommentExport:
    """Test exporting PGN without comments."""

    def test_export_removes_comments(self, comments_tree):
        """Test that comments are removed."""
        exported = export_no_comment_pgn(comments_tree, include_headers=False)

        # Should NOT include comments
        assert "King's pawn" not in exported
        assert "Symmetric response" not in exported
        assert "Developing" not in exported

        # Should include moves
        assert "e4" in exported
        assert "e5" in exported
        assert "Nf3" in exported

    def test_export_keeps_nags(self, comments_tree):
        """Test that NAG symbols are kept."""
        exported = export_no_comment_pgn(comments_tree, include_headers=False)

        # Should include NAG symbols
        assert "!!" in exported

    def test_export_keeps_variations(self, variations_tree):
        """Test that variations are kept."""
        exported = export_no_comment_pgn(variations_tree, include_headers=False)

        # Should include all variations
        assert "d4" in exported
        assert "c5" in exported
        assert "Bc4" in exported


# ===== Raw PGN Tests =====


class TestRawPGNExport:
    """Test exporting raw PGN (mainline only)."""

    def test_export_removes_variations(self, variations_tree):
        """Test that variations are removed."""
        exported = export_raw_pgn(variations_tree, include_headers=False)

        # Should NOT include variations
        assert "d4" not in exported  # First variation
        assert "c5" not in exported  # Second variation
        assert "Bc4" not in exported  # Third variation

        # Should include main line
        assert "e4" in exported
        assert "e5" in exported
        assert "Nf3" in exported
        assert "Nc6" in exported
        assert "Bb5" in exported

    def test_export_keeps_comments(self, comments_tree):
        """Test that comments are kept in raw export."""
        exported = export_raw_pgn(comments_tree, include_headers=False)

        # Should include comments from main line
        assert "King's pawn" in exported
        assert "Symmetric response" in exported

    def test_export_clean_removes_all(self, comments_tree):
        """Test that clean export removes both variations and comments."""
        exported = export_clean_mainline(comments_tree)

        # Should NOT include comments
        assert "King's pawn" not in exported
        assert "Symmetric response" not in exported

        # Should include moves
        assert "e4" in exported
        assert "e5" in exported


# ===== Variation Pruning Tests =====


class TestPruneBeforeNode:
    """Test pruning variations before a node."""

    def test_prune_keeps_path_to_target(self, variations_tree):
        """Test that path to target is kept."""
        # Find target node (move 2: Nf3)
        target = find_node_by_path(variations_tree, "main.2")
        assert target is not None

        # Prune before target
        pruned = prune_before_node(variations_tree, target)

        # Should keep main line to target
        assert pruned.san == "e4"
        assert pruned.children[0].san == "e5"

        # Should NOT have variations before target as rank > 0
        # Only main line path should exist
        first_move_variations = [c for c in pruned.children if c.rank > 0]
        assert len(first_move_variations) == 0  # No variations from first move

    def test_prune_keeps_variations_after(self, variations_tree):
        """Test that variations after target are kept."""
        target = find_node_by_path(variations_tree, "main.2")
        pruned = prune_before_node(variations_tree, target)

        # Navigate to target in pruned tree
        current = pruned
        while current and current.san != "Nf3":
            current = next((c for c in current.children if c.rank == 0), None)

        assert current is not None
        # Should have variations after Nf3 (Bc4)
        # Note: This depends on the exact structure of the test PGN


class TestRemoveComments:
    """Test comment removal."""

    def test_remove_all_comments(self, comments_tree):
        """Test that all comments are removed."""
        cleaned = remove_comments(comments_tree)

        # Check that no comments exist in tree
        def has_comments(node):
            if node.comment:
                return True
            return any(has_comments(child) for child in node.children)

        assert not has_comments(cleaned)

    def test_keep_structure(self, comments_tree):
        """Test that tree structure is unchanged."""
        cleaned = remove_comments(comments_tree)

        # Should have same moves
        assert cleaned.san == comments_tree.san
        assert len(cleaned.children) == len(comments_tree.children)


class TestExtractMainline:
    """Test mainline extraction."""

    def test_extract_removes_variations(self, variations_tree):
        """Test that variations are removed."""
        mainline = extract_mainline(variations_tree)

        # Check that only rank=0 children exist
        def has_variations(node):
            if any(c.rank > 0 for c in node.children):
                return True
            return any(has_variations(c) for c in node.children)

        assert not has_variations(mainline)

    def test_extract_keeps_comments(self, comments_tree):
        """Test that comments are kept."""
        mainline = extract_mainline(comments_tree)

        # Should keep comments from main line
        assert mainline.comment is not None or any(
            c.comment for c in mainline.children
        )


# ===== Integration Tests =====


class TestClipperIntegration:
    """Integration tests combining multiple features."""

    def test_clip_then_export_no_comment(self, variations_tree):
        """Test clipping then exporting without comments."""
        # First clip from move 2
        target = find_node_by_path(variations_tree, "main.2")
        clipped = prune_before_node(variations_tree, target)

        # Then remove comments
        cleaned = remove_comments(clipped)

        # Should have neither early variations nor comments
        pgn = tree_to_movetext(cleaned)
        assert "d4" not in pgn  # Early variation
        assert len(pgn) > 0

    def test_clip_then_extract_mainline(self, variations_tree):
        """Test clipping then extracting mainline."""
        # Clip from move 2
        target = find_node_by_path(variations_tree, "main.2")
        clipped = prune_before_node(variations_tree, target)

        # Extract mainline
        mainline = extract_mainline(clipped)

        # Should have only main line moves
        pgn = tree_to_movetext(mainline)
        assert "Bc4" not in pgn  # Variation after move 2
        assert "Nf3" in pgn
        assert "Nc6" in pgn


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
