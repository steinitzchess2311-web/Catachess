import pytest
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from unittest.mock import MagicMock

# Removed the import of Base and clear_sqlalchemy_metadata fixture
# because adapter functions now take VariationCls and MoveAnnotationCls as arguments.

from backend.core.real_pgn.models import NodeTree, PgnNode
from backend.modules.workspace.pgn_v2.adapters import (
    db_to_tree, tree_to_db_changes, NAG_MAP, REV_NAG_MAP,
    VariationPriority, VariationVisibility,  # Import redefined Enums
    ParentNotFoundError, InvalidMoveError, AdapterError  # Import error classes
)

# Mock DB Models for testing
@dataclass
class MockVariation:
    id: str
    chapter_id: str
    parent_id: Optional[str]
    next_id: Optional[str] = None
    move_number: int = 0
    color: str = "white"
    san: str = ""
    uci: str = ""
    fen: str = ""
    rank: int = 0
    priority: VariationPriority = VariationPriority.MAIN
    visibility: VariationVisibility = VariationVisibility.PUBLIC
    pinned: bool = False
    created_by: str = "test"
    version: int = 1

@dataclass
class MockMoveAnnotation:
    id: str
    move_id: str
    nag: Optional[str] = None
    text: Optional[str] = None
    author_id: str = "test"
    version: int = 1


# Helper to create a simple PgnNode
def create_pgn_node(node_id: str, parent_id: Optional[str], san: str, ply: int, move_number: int, fen: str, uci: str = "", main_child: Optional[str] = None, variations: List[str] = field(default_factory=list), comment_after: Optional[str] = None, nags: List[int] = field(default_factory=list)) -> PgnNode:
    return PgnNode(
        node_id=node_id, parent_id=parent_id, san=san, uci=uci, ply=ply, move_number=move_number, fen=fen,
        main_child=main_child, variations=variations, comment_after=comment_after, nags=nags
    )

# --- Tests for db_to_tree ---
def test_db_to_tree_empty_input():
    tree = db_to_tree([], [], MockVariation, MockMoveAnnotation)
    assert isinstance(tree, NodeTree)
    assert tree.root_id == "virtual_root"
    assert len(tree.nodes) == 1 # Only the virtual root node should exist

def test_db_to_tree_simple_mainline():
    chapter_id = "chap1"
    
    # DB data
    db_var1 = MockVariation(id="m1", chapter_id=chapter_id, parent_id=None, san="e4", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0)
    db_var2 = MockVariation(id="m2", chapter_id=chapter_id, parent_id="m1", san="e5", uci="e7e5", move_number=1, color="black", fen="fen2", rank=0)
    db_var3 = MockVariation(id="m3", chapter_id=chapter_id, parent_id="m2", san="Nf3", uci="g1f3", move_number=2, color="white", fen="fen3", rank=0)

    variations = [db_var1, db_var2, db_var3]
    annotations = []

    tree = db_to_tree(variations, annotations, MockVariation, MockMoveAnnotation)

    assert isinstance(tree, NodeTree)
    assert tree.root_id == "virtual_root"
    assert "virtual_root" in tree.nodes
    
    root_node = tree.nodes["virtual_root"]
    assert root_node.main_child == "m1"
    assert not root_node.variations

    n1 = tree.nodes["m1"]
    assert n1.san == "e4"
    assert n1.parent_id == "virtual_root" # db_to_tree should remap parent_id of db_root_moves
    assert n1.main_child == "m2"
    assert n1.ply == 1
    assert n1.move_number == 1

    n2 = tree.nodes["m2"]
    assert n2.san == "e5"
    assert n2.parent_id == "m1"
    assert n2.main_child == "m3"
    assert n2.ply == 2
    assert n2.move_number == 1

    n3 = tree.nodes["m3"]
    assert n3.san == "Nf3"
    assert n3.parent_id == "m2"
    assert n3.main_child is None # End of the line for now
    assert n3.ply == 3
    assert n3.move_number == 2

def test_db_to_tree_with_variations_and_annotations():
    chapter_id = "chap2"

    db_var1 = MockVariation(id="m1", chapter_id=chapter_id, parent_id=None, san="e4", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0)
    db_var2_main = MockVariation(id="m2m", chapter_id=chapter_id, parent_id="m1", san="e5", uci="e7e5", move_number=1, color="black", fen="fen2m", rank=0)
    db_var2_alt1 = MockVariation(id="m2a1", chapter_id=chapter_id, parent_id="m1", san="c5", uci="c7c5", move_number=1, color="black", fen="fen2a1", rank=1)
    db_var3_main = MockVariation(id="m3m", chapter_id=chapter_id, parent_id="m2m", san="Nf3", uci="g1f3", move_number=2, color="white", fen="fen3m", rank=0)

    db_anno_m1_text = MockMoveAnnotation(id="a1t", move_id="m1", text="Good start.")
    db_anno_m2m_nag = MockMoveAnnotation(id="a2n", move_id="m2m", nag="!")

    variations = [db_var1, db_var2_main, db_var2_alt1, db_var3_main]
    annotations = [db_anno_m1_text, db_anno_m2m_nag]

    tree = db_to_tree(variations, annotations, MockVariation, MockMoveAnnotation)

    assert tree.root_id == "virtual_root"
    
    n1 = tree.nodes["m1"]
    assert n1.san == "e4"
    assert n1.comment_after == "Good start."
    assert n1.nags == [] # Nag is attached to the move itself
    assert n1.main_child == "m2m"
    assert len(n1.variations) == 1 # Has one side variation (m2a1)

    n2m = tree.nodes["m2m"]
    assert n2m.san == "e5"
    assert n2m.nags == [NAG_MAP['!']]
    assert n2m.main_child == "m3m"

    n2a1 = tree.nodes["m2a1"]
    assert n2a1.san == "c5"
    assert n2a1.parent_id == "m1" # Parent of alt variation is m1
    assert n2a1.main_child is None # No next move in this short alt line

    n3m = tree.nodes["m3m"]
    assert n3m.san == "Nf3"
    assert n3m.parent_id == "m2m"

# --- Tests for tree_to_db_changes ---
def test_tree_to_db_changes_no_changes():
    chapter_id = "chap3"

    db_var1 = MockVariation(id="m1", chapter_id=chapter_id, parent_id=None, san="e4", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0)
    db_var2 = MockVariation(id="m2", chapter_id=chapter_id, parent_id="m1", san="e5", uci="e7e5", move_number=1, color="black", fen="fen2", rank=0)
    
    current_variations = [db_var1, db_var2]
    current_annotations = []
    
    # Build target tree from current DB state (should be identical)
    target_tree = db_to_tree(current_variations, current_annotations, MockVariation, MockMoveAnnotation)
    
    changes = tree_to_db_changes(target_tree, current_variations, current_annotations, MockVariation, MockMoveAnnotation)
    
    assert not changes["added_variations"]
    assert not changes["updated_variations"]
    assert not changes["deleted_variations"]
    assert not changes["added_annotations"]
    assert not changes["updated_annotations"]
    assert not changes["deleted_annotations"]

def test_tree_to_db_changes_add_move():
    chapter_id = "chap4"

    db_var1 = MockVariation(id="m1", chapter_id=chapter_id, parent_id=None, san="e4", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0)
    
    current_variations = [db_var1]
    current_annotations = []
    
    # Target tree: m1 -> m2 (new move)
    target_tree = db_to_tree(current_variations, current_annotations, MockVariation, MockMoveAnnotation)
    n1 = target_tree.nodes["m1"]
    
    # Manually add a new node to the tree
    new_m2_id = "new_m2"
    new_n2 = PgnNode(node_id=new_m2_id, parent_id="m1", san="e5", uci="e7e5", ply=2, move_number=1, fen="fen2", main_child=None, variations=[])
    target_tree.nodes[new_m2_id] = new_n2
    n1.main_child = new_m2_id # Link to parent

    changes = tree_to_db_changes(target_tree, current_variations, current_annotations, MockVariation, MockMoveAnnotation)
    
    assert len(changes["added_variations"]) == 1
    assert changes["added_variations"][0].id == new_m2_id
    assert changes["added_variations"][0].san == "e5"
    assert changes["added_variations"][0].parent_id == "m1"
    assert changes["added_variations"][0].rank == 0 # Should be main child
    assert not changes["updated_variations"]
    assert not changes["deleted_variations"]
    assert not changes["added_annotations"]

def test_tree_to_db_changes_update_move_and_add_annotation():
    chapter_id = "chap5"

    db_var1 = MockVariation(id="m1", chapter_id=chapter_id, parent_id=None, san="e4", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0)
    
    current_variations = [db_var1]
    current_annotations = []
    
    target_tree = db_to_tree(current_variations, current_annotations, MockVariation, MockMoveAnnotation)
    n1 = target_tree.nodes["m1"]
    
    # Update SAN and add a comment/NAG
    n1.san = "d4"
    n1.comment_after = "New opening"
    n1.nags.append(NAG_MAP['!'])

    changes = tree_to_db_changes(target_tree, current_variations, current_annotations, MockVariation, MockMoveAnnotation)
    
    assert len(changes["updated_variations"]) == 1
    assert changes["updated_variations"][0].id == "m1"
    assert changes["updated_variations"][0].san == "d4"

    assert len(changes["added_annotations"]) == 2 # One for text, one for NAG
    assert any(a.text == "New opening" for a in changes["added_annotations"])
    assert any(a.nag == "!" for a in changes["added_annotations"])

def test_tree_to_db_changes_delete_move():
    chapter_id = "chap6"

    db_var1 = MockVariation(id="m1", chapter_id=chapter_id, parent_id=None, san="e4", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0)
    db_var2 = MockVariation(id="m2", chapter_id=chapter_id, parent_id="m1", san="e5", uci="e7e5", move_number=1, color="black", fen="fen2", rank=0)
    
    current_variations = [db_var1, db_var2]
    current_annotations = []
    
    # Target tree: only m1, m2 deleted
    target_tree = NodeTree() # Empty tree means everything is deleted except virtual root
    target_tree.nodes["virtual_root"] = PgnNode(node_id="virtual_root", parent_id=None, san="<root>", uci="", ply=0, move_number=0, fen="fen0")
    target_tree.root_id = "virtual_root"
    target_tree.meta.headers["ChapterId"] = chapter_id # Add ChapterId for the test

    changes = tree_to_db_changes(target_tree, current_variations, current_annotations, MockVariation, MockMoveAnnotation)
    
    assert len(changes["deleted_variations"]) == 2
    assert {v.id for v in changes["deleted_variations"]} == {"m1", "m2"}

# --- Tests for error handling ---
def test_db_to_tree_parent_not_found():
    """Test that ParentNotFoundError is raised when a variation references non-existent parent."""
    chapter_id = "chap_err1"

    # Create a variation with a parent_id that doesn't exist
    db_var1 = MockVariation(
        id="m1", chapter_id=chapter_id, parent_id="non_existent_parent",
        san="e4", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0
    )

    with pytest.raises(ParentNotFoundError) as exc_info:
        db_to_tree([db_var1], [], MockVariation, MockMoveAnnotation)

    assert exc_info.value.node_id == "m1"
    assert exc_info.value.parent_id == "non_existent_parent"


def test_db_to_tree_missing_san():
    """Test that InvalidMoveError is raised when a move is missing SAN."""
    chapter_id = "chap_err2"

    db_var1 = MockVariation(
        id="m1", chapter_id=chapter_id, parent_id=None,
        san="", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0
    )

    with pytest.raises(InvalidMoveError) as exc_info:
        db_to_tree([db_var1], [], MockVariation, MockMoveAnnotation)

    assert exc_info.value.node_id == "m1"
    assert "SAN" in exc_info.value.reason


def test_db_to_tree_missing_uci():
    """Test that InvalidMoveError is raised when a move is missing UCI."""
    chapter_id = "chap_err3"

    db_var1 = MockVariation(
        id="m1", chapter_id=chapter_id, parent_id=None,
        san="e4", uci="", move_number=1, color="white", fen="fen1", rank=0
    )

    with pytest.raises(InvalidMoveError) as exc_info:
        db_to_tree([db_var1], [], MockVariation, MockMoveAnnotation)

    assert exc_info.value.node_id == "m1"
    assert "UCI" in exc_info.value.reason


# --- Tests for chapter headers/result ---
@dataclass
class MockChapter:
    """Mock Chapter for testing headers/result population."""
    id: str
    white: Optional[str] = None
    black: Optional[str] = None
    event: Optional[str] = None
    date: Optional[str] = None
    result: Optional[str] = None


def test_db_to_tree_with_chapter_headers():
    """Test that chapter headers/result are correctly populated."""
    chapter_id = "chap_header"

    chapter = MockChapter(
        id=chapter_id,
        white="Magnus Carlsen",
        black="Hikaru Nakamura",
        event="World Championship 2024",
        date="2024.01.15",
        result="1-0"
    )

    db_var1 = MockVariation(
        id="m1", chapter_id=chapter_id, parent_id=None,
        san="e4", uci="e2e4", move_number=1, color="white", fen="fen1", rank=0
    )

    tree = db_to_tree([db_var1], [], MockVariation, MockMoveAnnotation, chapter=chapter)

    assert tree.meta.headers["ChapterId"] == chapter_id
    assert tree.meta.headers["White"] == "Magnus Carlsen"
    assert tree.meta.headers["Black"] == "Hikaru Nakamura"
    assert tree.meta.headers["Event"] == "World Championship 2024"
    assert tree.meta.headers["Date"] == "2024.01.15"
    assert tree.meta.headers["Result"] == "1-0"
    assert tree.meta.result == "1-0"


def test_db_to_tree_with_setup_fen():
    """Test that setup_fen is correctly used for non-standard starting positions."""
    chapter_id = "chap_fen"
    custom_fen = "r1bqkbnr/pppppppp/2n5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 1 2"

    db_var1 = MockVariation(
        id="m1", chapter_id=chapter_id, parent_id=None,
        san="d4", uci="d2d4", move_number=2, color="white", fen="fen1", rank=0
    )

    tree = db_to_tree([db_var1], [], MockVariation, MockMoveAnnotation, setup_fen=custom_fen)

    assert tree.meta.setup_fen == custom_fen
    assert tree.nodes["virtual_root"].fen == custom_fen


# TODO: Add more tests for complex scenarios:
# - Reordering variations (rank changes)
# - Deleting annotations
# - Updating annotations (text/NAG changes)
# - Changing main_child (implies rank change for original main_child)
# - Full game with main line and multiple variations
