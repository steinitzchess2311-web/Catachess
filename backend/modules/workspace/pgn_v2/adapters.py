# This file is for Stage 2A of PGN implementation.
# It will contain adapters to convert between the database representation
# of a game tree and the `NodeTree` structure.

from typing import List, Dict, Any, Optional, Type
from collections import defaultdict
from enum import Enum # Import Enum for new definitions
from ulid import ULID # Import ULID

from backend.core.real_pgn.models import NodeTree, PgnNode
# from backend.modules.workspace.db.tables.variations import VariationPriority, VariationVisibility # REMOVED

# Redefine these enums to avoid importing the SQLAlchemy models
class VariationPriority(str, Enum):
    MAIN = "main"
    ALTERNATIVE = "alternative"
    DRAFT = "draft"

class VariationVisibility(str, Enum):
    PUBLIC = "public"
    MEMBERS = "members"
    PRIVATE = "private"

# NAG values are stored as strings in the DB (e.g., '!', '?'), 
# but PGN standard uses integer codes.
NAG_MAP = {
    '!': 1, '?': 2, '!!': 3, '??': 4, '!?': 5, '?!': 6
}
REV_NAG_MAP = {v: k for k, v in NAG_MAP.items()}

def _ply_to_color(ply: int) -> str:
    return 'white' if ply % 2 == 1 else 'black'

class AdapterError(Exception):
    """Base exception for adapter errors."""
    pass


class ParentNotFoundError(AdapterError):
    """Raised when a variation references a non-existent parent."""
    def __init__(self, node_id: str, parent_id: str):
        self.node_id = node_id
        self.parent_id = parent_id
        super().__init__(f"Node '{node_id}' references non-existent parent '{parent_id}'")


class InvalidMoveError(AdapterError):
    """Raised when a move is invalid (e.g., missing required fields)."""
    def __init__(self, node_id: str, reason: str):
        self.node_id = node_id
        self.reason = reason
        super().__init__(f"Invalid move '{node_id}': {reason}")


def db_to_tree(
    variations: List[Any],
    annotations: List[Any],
    VariationCls: Type,
    MoveAnnotationCls: Type,
    chapter: Optional[Any] = None,
    setup_fen: Optional[str] = None,
) -> NodeTree:
    """
    Converts lists of Variation and MoveAnnotation DB objects into a NodeTree.

    Args:
        variations: List of Variation DB objects
        annotations: List of MoveAnnotation DB objects
        VariationCls: The Variation class (for type checking)
        MoveAnnotationCls: The MoveAnnotation class (for type checking)
        chapter: Optional Chapter object to populate headers/result
        setup_fen: Optional FEN for non-standard starting position

    Returns:
        NodeTree with nodes and metadata populated

    Raises:
        ParentNotFoundError: If a variation references a non-existent parent
        InvalidMoveError: If a move is missing required fields (san, uci)
    """
    tree = NodeTree()

    # Use standard starting position or custom setup FEN
    start_fen = setup_fen or "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    if setup_fen:
        tree.meta.setup_fen = setup_fen

    # 1. Initialize virtual root node
    virtual_root_id = "virtual_root"
    virtual_root_node = PgnNode(
        node_id=virtual_root_id,
        parent_id=None,
        san="<root>",
        uci="<root>",
        ply=0,
        move_number=0,
        fen=start_fen
    )
    tree.nodes[virtual_root_id] = virtual_root_node
    tree.root_id = virtual_root_id

    # 2. Populate headers from chapter if provided
    if chapter:
        if hasattr(chapter, 'id'):
            tree.meta.headers["ChapterId"] = chapter.id
        if hasattr(chapter, 'white') and chapter.white:
            tree.meta.headers["White"] = chapter.white
        if hasattr(chapter, 'black') and chapter.black:
            tree.meta.headers["Black"] = chapter.black
        if hasattr(chapter, 'event') and chapter.event:
            tree.meta.headers["Event"] = chapter.event
        if hasattr(chapter, 'date') and chapter.date:
            tree.meta.headers["Date"] = chapter.date
        if hasattr(chapter, 'result') and chapter.result:
            tree.meta.result = chapter.result
            tree.meta.headers["Result"] = chapter.result

    if not variations:
        return tree



    # 3. Process annotations into a lookup map
    annotation_map = defaultdict(lambda: {"nags": [], "text": None})
    for anno in annotations:
        if anno.nag and anno.nag in NAG_MAP:
            annotation_map[anno.move_id]["nags"].append(NAG_MAP[anno.nag])
        if anno.text:
            annotation_map[anno.move_id]["text"] = anno.text

    # 4. Build a set of all variation IDs for parent validation
    all_variation_ids = {var.id for var in variations}

    # 5. Create all PgnNode objects and group children by parent
    nodes = {virtual_root_id: virtual_root_node}  # Start with virtual root
    children_by_parent = defaultdict(list)  # Stores DB Variation objects

    for var in variations:
        # Validate move has required fields
        if not var.san:
            raise InvalidMoveError(var.id, "missing SAN notation")
        if not var.uci:
            raise InvalidMoveError(var.id, "missing UCI notation")

        # Validate parent exists (if specified)
        if var.parent_id is not None and var.parent_id not in all_variation_ids:
            raise ParentNotFoundError(var.id, var.parent_id)

        ply = var.move_number * 2 - (1 if var.color == 'white' else 0)

        anno = annotation_map[var.id]
        parent_id_for_node = var.parent_id
        if var.parent_id is None:  # If it's a DB root move, its parent in NodeTree is the virtual root
            parent_id_for_node = virtual_root_id

        node = PgnNode(
            node_id=var.id,
            parent_id=parent_id_for_node,
            san=var.san,
            uci=var.uci,
            ply=ply,
            move_number=var.move_number,
            comment_after=anno["text"],
            nags=anno["nags"],
            fen=var.fen
        )
        nodes[var.id] = node
        if var.parent_id:
            children_by_parent[var.parent_id].append(var)
        else:  # This is a DB root move
            children_by_parent[virtual_root_id].append(var)  # Link DB root moves to virtual root

    # 6. Link children to parents (main_child vs variations)
    # Process children of the virtual root specifically (these are DB root moves)

    db_root_moves = children_by_parent[virtual_root_id]

    db_root_moves.sort(key=lambda v: v.rank)

    if db_root_moves:

        virtual_root_node.main_child = db_root_moves[0].id

        virtual_root_node.variations = [v.id for v in db_root_moves[1:]]



    # Process children of actual DB moves

    for parent_var_id, children_vars in children_by_parent.items():

        if parent_var_id == virtual_root_id: # Already handled

            continue

        if parent_var_id not in nodes: # Should not happen if data is consistent

            continue

        

        parent_node = nodes[parent_var_id]

        children_vars.sort(key=lambda v: v.rank)

        

        if children_vars:

            parent_node.main_child = children_vars[0].id

            parent_node.variations = [v.id for v in children_vars[1:]]



    tree.nodes = nodes

    # Fallback: If ChapterId not set via chapter param, get from first variation
    if "ChapterId" not in tree.meta.headers and variations:
        tree.meta.headers["ChapterId"] = variations[0].chapter_id

    return tree

def tree_to_db_changes(tree: NodeTree, current_variations: List[Any], current_annotations: List[Any], VariationCls: Type, MoveAnnotationCls: Type, actor_id: str) -> Dict[str, List[Any]]:
    """
    Compares a NodeTree to the database state and generates a list of
    incremental changes (adds, updates, deletes).
    """
    changes = {
        "added_variations": [], "updated_variations": [], "deleted_variations": [],
        "added_annotations": [], "updated_annotations": [], "deleted_annotations": []
    }

    # 1. Create lookups for current DB state
    current_variation_map = {v.id: v for v in current_variations}
    current_annotation_map = defaultdict(list)
    for anno in current_annotations:
        current_annotation_map[anno.move_id].append(anno)

    # 2. Convert current DB state to a NodeTree for easy comparison (baseline)
    baseline_tree = db_to_tree(current_variations, current_annotations, VariationCls, MoveAnnotationCls)
    baseline_node_map = baseline_tree.nodes

    # Helper to convert PgnNode to Variation object
    def _pgn_node_to_variation(pgn_node: PgnNode, chapter_id: str, rank: int, next_id: Optional[str], actor_id: str) -> Any: # Returns Type
        return VariationCls(
            id=pgn_node.node_id,
            chapter_id=chapter_id,
            parent_id=pgn_node.parent_id,
            next_id=next_id,
            move_number=pgn_node.move_number,
            color=_ply_to_color(pgn_node.ply),
            san=pgn_node.san,
            uci=pgn_node.uci,
            fen=pgn_node.fen,
            rank=rank,
            # Default other fields, as they are not in PgnNode directly
            priority=VariationPriority.MAIN,
            visibility=VariationVisibility.PUBLIC,
            pinned=False,
            created_by=actor_id,
            version=1
        )
    
    # Helper to convert PgnNode comment/nags to MoveAnnotation objects
    def _pgn_node_to_annotations(pgn_node: PgnNode, actor_id: str) -> List[Any]: # Returns List[Type]
        annos = []
        if pgn_node.comment_after:
            annos.append(MoveAnnotationCls(
                id=str(ULID()), # New ID for new annotation
                move_id=pgn_node.node_id,
                text=pgn_node.comment_after,
                author_id=actor_id,
                version=1
            ))
        for nag_int in pgn_node.nags:
            nag_str = REV_NAG_MAP.get(nag_int)
            if nag_str:
                annos.append(MoveAnnotationCls(
                    id=str(ULID()), # New ID
                    move_id=pgn_node.node_id,
                    nag=nag_str,
                    author_id=actor_id,
                    version=1
                ))
        return annos

    chapter_id = tree.meta.headers.get("ChapterId") # Assuming chapter_id is stored in meta
    if not chapter_id:
        raise ValueError("NodeTree must contain ChapterId in its meta headers for DB conversion.")

    # Iterate through desired NodeTree nodes to find added/updated variations and annotations
    for node_id, pgn_node in tree.nodes.items():
        if node_id == "virtual_root": # Skip the virtual root node
            continue

        current_var = current_variation_map.get(node_id)
        current_annos = current_annotation_map.get(node_id, [])

        # Get target rank and next_id for this PgnNode
        # This requires traversing the parent in the target tree to determine rank and next_id
        target_rank = 0
        target_next_id = None
        if pgn_node.parent_id and pgn_node.parent_id != "virtual_root":
            parent_pgn_node = tree.nodes.get(pgn_node.parent_id)
            if parent_pgn_node:
                if parent_pgn_node.main_child == node_id:
                    target_rank = 0
                    if parent_pgn_node.main_child: # If this is main child, its next is parent's next
                        # this logic is tricky, next_id is for *mainline* next move
                        # it's better to build this by traversing in the other direction.
                        # For now, let's simplify and set next_id based on a linear walk.
                        pass
                else:
                    try:
                        target_rank = parent_pgn_node.variations.index(node_id) + 1 # Rank 1 for first variation etc.
                    except ValueError:
                        pass # Should not happen if data is consistent

        # Check for added/updated variations
        if not current_var:
            # Added variation
            # We need to compute next_id for the added variation during a final pass.
            changes["added_variations"].append(_pgn_node_to_variation(pgn_node, chapter_id, target_rank, None, actor_id))
        else:
            # Check for updated variation fields
            # Simplified comparison for now, full comparison would be field by field
            # next_id is very complex to handle here without full tree context
            # Let's just compare basic fields for now
            updated = False
            # Handle virtual_root mapping: DB uses None for root moves, NodeTree uses "virtual_root"
            db_parent_id = current_var.parent_id
            tree_parent_id = pgn_node.parent_id
            if tree_parent_id == "virtual_root":
                tree_parent_id = None  # Normalize for comparison
            if db_parent_id != tree_parent_id: updated = True
            if current_var.san != pgn_node.san: updated = True
            if current_var.uci != pgn_node.uci: updated = True
            if current_var.fen != pgn_node.fen: updated = True
            if current_var.rank != target_rank: updated = True # Compare current rank with target rank
            
            if updated:
                updated_var = _pgn_node_to_variation(pgn_node, chapter_id, target_rank, current_var.next_id, actor_id)
                updated_var.id = current_var.id # Ensure ID is preserved for update
                changes["updated_variations"].append(updated_var)

        # Check for added/updated/deleted annotations
        target_annos = _pgn_node_to_annotations(pgn_node, actor_id)
        
        # This is very simplified, real diffing of annotations is harder
        # For now, just mark all old as deleted, all new as added if different
        if (pgn_node.comment_after and not any(a.text == pgn_node.comment_after for a in current_annos)) or \
           (pgn_node.nags and not any(REV_NAG_MAP.get(n) in [a.nag for a in current_annos] for n in pgn_node.nags)):
            # If target has comment/nags and current doesn't match, delete all old and add all new
            for old_anno in current_annos:
                changes["deleted_annotations"].append(old_anno)
            for new_anno in target_annos:
                changes["added_annotations"].append(new_anno)
        elif not pgn_node.comment_after and not pgn_node.nags and current_annos:
            # If target has no comment/nags but current has, delete all old
            for old_anno in current_annos:
                changes["deleted_annotations"].append(old_anno)


    # Identify deleted variations (those in baseline_tree but not in target tree)
    for baseline_node_id, baseline_pgn_node in baseline_node_map.items():
        if baseline_node_id == "virtual_root":
            continue
        if baseline_node_id not in tree.nodes:
            changes["deleted_variations"].append(current_variation_map[baseline_node_id])
            # Also delete associated annotations
            for old_anno in current_annotation_map.get(baseline_node_id, []):
                changes["deleted_annotations"].append(old_anno)

    # FINAL PASS: Compute 'next_id' for added/updated variations based on tree structure
    # This ensures correct linking for linear playback
    # Build a temporary map of all nodes that are being added/updated for quick lookup
    all_affected_nodes = {var.id: var for var_list in changes.values() if isinstance(var_list, list) for var in var_list if hasattr(var, 'id')}

    for node_id, pgn_node in tree.nodes.items():
        if node_id == "virtual_root":
            continue

        target_next_id = None
        # If it's a main_child, its next_id is the main_child of itself
        if pgn_node.main_child:
            target_next_id = pgn_node.main_child
        elif pgn_node.parent_id and pgn_node.parent_id != "virtual_root":
            # If it's a variation, find its next sibling in the parent's variations
            parent_pgn_node = tree.nodes.get(pgn_node.parent_id)
            if parent_pgn_node and parent_pgn_node.variations:
                try:
                    current_index = parent_pgn_node.variations.index(node_id)
                    if current_index < len(parent_pgn_node.variations) - 1:
                        target_next_id = parent_pgn_node.variations[current_index + 1]
                except ValueError:
                    pass # Node not found in parent's variations, shouldn't happen with consistent data
        
        # Apply target_next_id to variations that are being added or updated
        if node_id in all_affected_nodes:
            # Find the actual object in the changes list and update its next_id
            for var_list in [changes["added_variations"], changes["updated_variations"]]:
                for var in var_list:
                    if var.id == node_id:
                        var.next_id = target_next_id
                        break

    return changes
