"""
PGN Cleaner - Core innovation: Clip PGN from a specific move.

This module implements the key feature:
"Copy from this move" - Remove variations before a specific move,
but keep all variations after it.

Example:
    Original PGN:
        1. e4 (1. d4) e5 (1...c5 2. Nf3) 2. Nf3 (2. Bc4) Nc6 3. Bb5

    Clipping from "2. Nf3":
        1. e4 e5 2. Nf3 (2. Bc4) Nc6 3. Bb5

    Result:
    - Variations before Nf3 (d4, c5) are removed
    - Only mainline path to Nf3 is kept
    - All variations after Nf3 (Bc4) are preserved
"""

from workspace.pgn.cleaner.variation_pruner import (
    MovePath,
    find_node_by_path,
    prune_before_node,
)
from workspace.pgn.serializer.to_pgn import tree_to_pgn, tree_to_movetext
from workspace.pgn.serializer.to_tree import VariationNode


def clip_pgn_from_move(
    root: VariationNode,
    move_path: str | MovePath,
    headers: dict[str, str] | None = None,
    include_headers: bool = True,
) -> str:
    """
    Clip PGN starting from a specific move.

    This is the core innovation: Create a PGN that:
    1. Excludes all variations BEFORE the target move
    2. Keeps only the mainline path TO the target move
    3. Preserves ALL variations AFTER the target move

    Args:
        root: Root of the variation tree
        move_path: Path to the move to clip from (e.g., "main.12" or "main.5.var1.2")
        headers: Optional PGN headers
        include_headers: Whether to include headers in output

    Returns:
        PGN text starting from the specified move

    Raises:
        ValueError: If move_path is invalid or node not found

    Examples:
        >>> # Clip from move 12 in main line
        >>> pgn = clip_pgn_from_move(root, "main.12")

        >>> # Clip from 2nd move in first variation of move 5
        >>> pgn = clip_pgn_from_move(root, "main.5.var1.2")

        >>> # Clip without headers (for copying to clipboard)
        >>> pgn = clip_pgn_from_move(root, "main.12", include_headers=False)
    """
    # Find target node
    target = find_node_by_path(root, move_path)
    if target is None:
        path_str = str(move_path) if isinstance(move_path, MovePath) else move_path
        raise ValueError(f"Node not found at path: {path_str}")

    # Create new tree with variations pruned before target
    clipped_tree = prune_before_node(root, target)

    # Generate PGN
    if include_headers:
        return tree_to_pgn(clipped_tree, headers=headers)
    else:
        return tree_to_movetext(clipped_tree)


def clip_pgn_from_move_to_clipboard(
    root: VariationNode,
    move_path: str | MovePath,
) -> str:
    """
    Clip PGN for clipboard (no headers, ready to paste).

    Args:
        root: Root of the variation tree
        move_path: Path to the move to clip from

    Returns:
        PGN movetext only (no headers)

    Example:
        >>> movetext = clip_pgn_from_move_to_clipboard(root, "main.12")
        >>> # Can be pasted directly into chess software
    """
    return clip_pgn_from_move(root, move_path, include_headers=False)


def clip_pgn_from_node(
    root: VariationNode,
    target: VariationNode,
    headers: dict[str, str] | None = None,
    include_headers: bool = True,
) -> str:
    """
    Clip PGN starting from a specific node object.

    Same as clip_pgn_from_move but takes a node directly instead of path.

    Args:
        root: Root of the variation tree
        target: Target node to clip from
        headers: Optional PGN headers
        include_headers: Whether to include headers in output

    Returns:
        PGN text starting from the target node

    Example:
        >>> node = find_node_by_path(root, "main.12")
        >>> pgn = clip_pgn_from_node(root, node)
    """
    # Create new tree with variations pruned before target
    clipped_tree = prune_before_node(root, target)

    # Generate PGN
    if include_headers:
        return tree_to_pgn(clipped_tree, headers=headers)
    else:
        return tree_to_movetext(clipped_tree)


def get_clip_preview(
    root: VariationNode,
    move_path: str | MovePath,
    max_moves: int = 5,
) -> dict[str, any]:
    """
    Get a preview of what will be clipped.

    Useful for showing users what they're about to copy.

    Args:
        root: Root of the variation tree
        move_path: Path to the move to clip from
        max_moves: Maximum number of moves to show in preview

    Returns:
        Dictionary with preview information:
        - target_move: The move being clipped from
        - moves_before: Number of moves that will be removed
        - moves_after: Number of moves that will be kept
        - variations_removed: Number of variations before target
        - variations_kept: Number of variations after target
        - preview_text: Short preview of the result

    Example:
        >>> preview = get_clip_preview(root, "main.12")
        >>> print(preview["preview_text"])
        "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6..."
    """
    # Find target node
    target = find_node_by_path(root, move_path)
    if target is None:
        path_str = str(move_path) if isinstance(move_path, MovePath) else move_path
        raise ValueError(f"Node not found at path: {path_str}")

    # Count moves and variations
    moves_before = _count_moves_to_node(root, target)
    moves_after = _count_moves_from_node(target)

    variations_removed = _count_variations_before_node(root, target)

    # Create clipped tree for counting kept variations
    clipped_tree = prune_before_node(root, target)
    variations_kept = _count_all_variations(clipped_tree)

    # Generate preview text
    preview_pgn = clip_pgn_from_move(root, move_path, include_headers=False)
    preview_lines = preview_pgn.split("\n")
    preview_text = preview_lines[0][:100] + "..." if preview_lines[0] else ""

    return {
        "target_move": f"{target.move_number}. {target.san}",
        "moves_before": moves_before,
        "moves_after": moves_after,
        "variations_removed": variations_removed,
        "variations_kept": variations_kept,
        "preview_text": preview_text,
    }


def _count_moves_to_node(root: VariationNode, target: VariationNode) -> int:
    """Count moves from root to target."""
    count = 0
    current = root

    while current and current is not target:
        count += 1
        # Follow main line
        main_child = next((c for c in current.children if c.rank == 0), None)
        current = main_child

    return count


def _count_moves_from_node(node: VariationNode) -> int:
    """Count total moves in subtree."""
    count = 1  # Count this node

    for child in node.children:
        count += _count_moves_from_node(child)

    return count


def _count_variations_before_node(root: VariationNode, target: VariationNode) -> int:
    """Count variations before target node."""
    count = 0
    current = root

    while current and current is not target:
        # Count alternative variations (rank > 0)
        count += sum(1 for c in current.children if c.rank > 0)

        # Follow main line
        main_child = next((c for c in current.children if c.rank == 0), None)
        current = main_child

    return count


def _count_all_variations(node: VariationNode) -> int:
    """Count all variations in subtree."""
    count = sum(1 for c in node.children if c.rank > 0)

    for child in node.children:
        count += _count_all_variations(child)

    return count
