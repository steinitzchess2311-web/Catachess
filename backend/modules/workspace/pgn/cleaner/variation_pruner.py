"""
Variation tree navigation and pruning utilities.

This module provides utilities for:
- Navigating variation trees using move paths (e.g., "main.12.var2.3")
- Finding specific nodes in the tree
- Pruning variations according to various rules
- Creating subtrees from specific positions
"""

from dataclasses import dataclass
import logging
import re
from typing import Literal

from workspace.pgn.serializer.to_tree import VariationNode

logger = logging.getLogger(__name__)


@dataclass
class MovePath:
    """
    Represents a path to a specific move in the variation tree.

    Format: "main.12.var2.3" means:
    - Start at main line
    - Go to move 12 (counting from 1)
    - Take variation 2 (rank=2, first alternative after rank=1)
    - Go to move 3 in that variation

    Components:
    - segments: List of (segment_type, index) tuples
      - ("main", move_index): Main line move
      - ("var", variation_rank): Alternative variation

    Examples:
    - "main.1" -> First move in main line
    - "main.5.var1.2" -> 2nd move in first variation starting from move 5
    - "main.3.var1.4.var2.1" -> Nested variations
    """

    segments: list[tuple[Literal["main", "var"], int]]

    def __str__(self) -> str:
        """String representation of the path."""
        if not self.segments:
            return ""

        parts = []
        for i, (seg_type, index) in enumerate(self.segments):
            if seg_type == "main":
                # First segment or after a variation needs "main" prefix
                if i == 0:
                    parts.append(f"main.{index}")
                else:
                    # Check if previous was a variation
                    prev_type = self.segments[i - 1][0]
                    if prev_type == "var":
                        parts.append(str(index))
                    else:
                        # This shouldn't happen in valid paths
                        parts.append(f"main.{index}")
            else:
                parts.append(f"var{index}")
        return ".".join(parts)

    @classmethod
    def from_string(cls, path_str: str) -> "MovePath":
        """
        Parse a move path string.

        Args:
            path_str: Path string like "main.12.var2.3"

        Returns:
            MovePath object

        Raises:
            ValueError: If path string is invalid
        """
        return parse_move_path(path_str)


def parse_move_path(path_str: str) -> MovePath:
    """
    Parse a move path string into a MovePath object.

    Args:
        path_str: Path string like "main.12.var2.3"

    Returns:
        MovePath object

    Raises:
        ValueError: If path string is invalid

    Examples:
        >>> parse_move_path("main.1")
        MovePath(segments=[("main", 1)])

        >>> parse_move_path("main.5.var1.2")
        MovePath(segments=[("main", 5), ("var", 1), ("main", 2)])
    """
    if not path_str:
        raise ValueError("Path string cannot be empty")

    parts = path_str.split(".")
    segments = []

    i = 0
    while i < len(parts):
        part = parts[i]

        if part == "main":
            # Next part should be a move number
            if i + 1 >= len(parts):
                raise ValueError(f"Expected move number after 'main' at position {i}")

            try:
                move_num = int(parts[i + 1])
            except ValueError:
                raise ValueError(
                    f"Expected integer move number, got '{parts[i + 1]}' at position {i + 1}"
                )

            if move_num < 1:
                raise ValueError(f"Move number must be >= 1, got {move_num}")

            segments.append(("main", move_num))
            i += 2

        elif part.startswith("var"):
            # Extract variation rank
            try:
                var_rank = int(part[3:])  # Skip "var" prefix
            except ValueError:
                raise ValueError(f"Invalid variation format '{part}' at position {i}")

            if var_rank < 1:
                raise ValueError(f"Variation rank must be >= 1, got {var_rank}")

            segments.append(("var", var_rank))

            # Next part should be a move number
            if i + 1 >= len(parts):
                raise ValueError(
                    f"Expected move number after variation at position {i}"
                )

            try:
                move_num = int(parts[i + 1])
            except ValueError:
                raise ValueError(
                    f"Expected integer move number, got '{parts[i + 1]}' at position {i + 1}"
                )

            if move_num < 1:
                raise ValueError(f"Move number must be >= 1, got {move_num}")

            segments.append(("main", move_num))
            i += 2

        else:
            raise ValueError(f"Unexpected path component '{part}' at position {i}")

    return MovePath(segments=segments)


def format_move_path(segments: list[tuple[Literal["main", "var"], int]]) -> str:
    """
    Format a list of path segments into a path string.

    Args:
        segments: List of (segment_type, index) tuples

    Returns:
        Formatted path string

    Examples:
        >>> format_move_path([("main", 1)])
        'main.1'

        >>> format_move_path([("main", 5), ("var", 1), ("main", 2)])
        'main.5.var1.2'
    """
    path = MovePath(segments=segments)
    return str(path)


def find_node_by_path(
    root: VariationNode | None, path: MovePath | str
) -> VariationNode | None:
    """
    Find a node in the variation tree by its path.

    Move numbers refer to full move numbers. For example:
    - "main.1" = first move (1. e4)
    - "main.3" = third move (3. Bb5)

    Args:
        root: Root of the variation tree
        path: MovePath object or path string

    Returns:
        The node at the specified path, or None if not found

    Examples:
        >>> root = pgn_to_tree(pgn_text)
        >>> node = find_node_by_path(root, "main.1")
        >>> node.san
        'e4'

        >>> node = find_node_by_path(root, "main.2.var1.1")
        >>> node.san  # First move in first variation from move 2
        'c5'
    """
    if root is None:
        return None

    # Convert string to MovePath if needed
    if isinstance(path, str):
        black_match = _parse_black_move_notation(path)
        if black_match:
            move_number, san = black_match
            return _find_black_move_by_san(root, move_number, san)
        path = parse_move_path(path)

    current = root
    in_variation = False
    parent: VariationNode | None = None
    parents: list[VariationNode] = []
    failed = False

    for seg_type, index in path.segments:
        print(f"DEBUG: Segment {seg_type}.{index} | Current: {current} | Parent: {parent}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Traversing path segment: %s.%s (current=%s, move=%s%s)",
                seg_type,
                index,
                current.san,
                current.move_number,
                "..." if current.color == "black" else ".",
            )
        if seg_type == "main":
            if in_variation:
                if index < 1:
                    return None
                if index == 1:
                    # Stay at current node, don't update parent
                    continue
                steps = index - 1
                while steps > 0:
                    main_child = next(
                        (child for child in current.children if child.rank == 0),
                        None,
                    )
                    if main_child is None:
                        failed = True
                        break
                    parent = current
                    parents.append(current)
                    current = main_child
                    steps -= 1
                if failed:
                    break
                continue

            # Navigate to the move with the specified move_number (white move)
            target_move_num = index
            if (
                current.move_number == target_move_num
                and current.color == "white"
            ):
                continue

            while current is not None:
                if (
                    current.move_number == target_move_num
                    and current.color == "white"
                ):
                    break
                main_child = next(
                    (child for child in current.children if child.rank == 0), None
                )
                if main_child is None:
                    failed = True
                    break
                parent = current
                parents.append(current)
                current = main_child

            if failed or current is None or current.move_number != target_move_num:
                failed = True
                break

        elif seg_type == "var":
            var_rank = index
            var_child = _select_variation_child(current, parent, var_rank)
            if var_child is None:
                failed = True
                break
            
            # If var_child is a direct child of current, update parent to current.
            # If var_child is a sibling (child of parent), keep parent as is.
            if var_child in current.children:
                parent = current
            
            current = var_child
            in_variation = True

    if failed:
        return _find_node_by_path_bfs(root, path)

    if current is None:
        return None

    return current


def _find_node_by_path_bfs(
    root: VariationNode, path: MovePath
) -> VariationNode | None:
    queue = [root]
    while queue:
        node = queue.pop(0)
        node_path = get_path_to_node(root, node)
        if node_path and node_path.segments == path.segments:
            return node
        queue.extend(node.children)
    return None


def _select_variation_child(
    current: VariationNode, parent: VariationNode | None, var_rank: int
) -> VariationNode | None:
    if var_rank < 1:
        return None

    same_ply_children = [
        child
        for child in current.children
        if child.move_number == current.move_number and child.color == current.color
    ]
    same_ply_children.sort(key=lambda child: child.rank)
    if var_rank <= len(same_ply_children):
        return same_ply_children[var_rank - 1]

    direct_child = next(
        (child for child in current.children if child.rank == var_rank), None
    )
    if direct_child is not None:
        return direct_child

    if parent is not None:
        siblings = [
            child
            for child in parent.children
            if child is not current
            and child.rank > current.rank
            and child.move_number == current.move_number
            and child.color == current.color
        ]
        siblings.sort(key=lambda child: child.rank)
        if var_rank <= len(siblings):
            return siblings[var_rank - 1]

    return None


def _parse_black_move_notation(path_str: str) -> tuple[int, str] | None:
    match = re.match(r"^main\.(\d+)\.\.\.(\S+)$", path_str.strip())
    if not match:
        return None
    move_number = int(match.group(1))
    san = match.group(2)
    if move_number < 1:
        return None
    return move_number, san


def _find_black_move_by_san(
    root: VariationNode, move_number: int, san: str
) -> VariationNode | None:
    queue = [root]
    while queue:
        node = queue.pop(0)
        if (
            node.color == "black"
            and node.move_number == move_number
            and node.san == san
        ):
            return node
        queue.extend(node.children)
    return None


def get_path_to_node(
    root: VariationNode, target: VariationNode
) -> MovePath | None:
    """
    Find the path from root to a target node.

    Args:
        root: Root of the variation tree
        target: Target node to find

    Returns:
        MovePath to the target, or None if target not in tree

    Note:
        This performs a breadth-first search to find the target node,
        then reconstructs the path.
    """
    # BFS to find target and track parents
    queue = [(root, [])]

    while queue:
        node, path = queue.pop(0)

        if node is target:
            return MovePath(segments=path) if path else None

        # Add children to queue
        for child in node.children:
            new_path = path.copy()

            if child.rank == 0:
                # Main line continuation
                # Determine move number
                if not new_path:
                    # First move
                    new_path.append(("main", 1))
                else:
                    # Increment move count
                    last_seg_type, last_index = new_path[-1]
                    if last_seg_type == "main":
                        new_path.append(("main", last_index + 1))
                    else:
                        new_path.append(("main", 1))
            else:
                # Variation
                new_path.append(("var", child.rank))
                new_path.append(("main", 1))

            queue.append((child, new_path))

    return None


def copy_tree(node: VariationNode) -> VariationNode:
    """
    Create a deep copy of a variation tree.
    Iterative implementation.

    Args:
        node: Root node to copy

    Returns:
        Deep copy of the tree
    """
    root_copy = VariationNode(
        move_number=node.move_number,
        color=node.color,
        san=node.san,
        uci=node.uci,
        fen=node.fen,
        nag=node.nag,
        comment=node.comment,
        rank=node.rank,
    )
    
    stack = [(node, root_copy)]
    while stack:
        src, dst = stack.pop()
        for child in src.children:
            child_copy = VariationNode(
                move_number=child.move_number,
                color=child.color,
                san=child.san,
                uci=child.uci,
                fen=child.fen,
                nag=child.nag,
                comment=child.comment,
                rank=child.rank,
            )
            dst.children.append(child_copy)
            stack.append((child, child_copy))

    return root_copy


def prune_before_node(
    root: VariationNode, target: VariationNode
) -> VariationNode:
    """
    Create a new tree that starts from target node, removing all variations
    before it but keeping the main line path to it.

    Args:
        root: Root of the variation tree
        target: Target node to start from

    Returns:
        New tree starting from target, with mainline path preserved

    Example:
        Original tree:
            1. e4 (1. d4) e5 (1...c5 2. Nf3) 2. Nf3 Nc6

        If target is the move "Nf3" (white's 2nd move):
            1. e4 e5 2. Nf3 Nc6

        All variations before Nf3 are removed, but the path to it is kept.
    """
    def find_path_nodes(
        node: VariationNode, target_node: VariationNode
    ) -> list[VariationNode] | None:
        # Iterative path finding
        # Stack: (node, path_so_far)
        stack = [(node, [node])]
        while stack:
            curr, path = stack.pop()
            if curr is target_node:
                return path
            
            for child in curr.children:
                stack.append((child, path + [child]))
        return None

    path_nodes = find_path_nodes(root, target)
    if not path_nodes:
        return _copy_tree_with_normalized_ranks(target, rank=0)

    new_root = _copy_node_with_rank(path_nodes[0], rank=0)
    current_new = new_root

    # For all nodes on path except the last one (parent of target)
    for i in range(1, len(path_nodes) - 1):
        node = path_nodes[i]
        new_child = _copy_node_with_rank(node, rank=0)
        current_new.children = [new_child]
        current_new = new_child

    # For the parent of target (which is path_nodes[-2] if target is not root)
    if len(path_nodes) >= 2:
        parent = path_nodes[-2]
        
        # We need to keep the target AND all its siblings (alternatives at this ply)
        target_siblings_and_self = [
            child for child in parent.children
            if child.move_number == target.move_number and child.color == target.color
        ]
        
        new_children = []
        for index, child in enumerate(sorted(target_siblings_and_self, key=lambda x: x.rank)):
            # Keep sibling/target and its full subtree
            child_copy = _copy_tree_with_normalized_ranks(child, rank=index)
            new_children.append(child_copy)
        
        current_new.children = new_children
    else:
        # Target is root, just return target's subtree
        return _copy_tree_with_normalized_ranks(target, rank=0)

    return new_root


def _copy_node_with_rank(node: VariationNode, rank: int) -> VariationNode:
    return VariationNode(
        move_number=node.move_number,
        color=node.color,
        san=node.san,
        uci=node.uci,
        fen=node.fen,
        nag=node.nag,
        comment=node.comment,
        rank=rank,
    )


def _copy_tree_with_normalized_ranks(
    node: VariationNode, rank: int
) -> VariationNode:
    """Iterative version of copying with rank normalization."""
    root_copy = _copy_node_with_rank(node, rank=rank)
    
    # Stack: (src_node, dst_node)
    stack = [(node, root_copy)]
    while stack:
        src, dst = stack.pop()
        children_sorted = sorted(src.children, key=lambda child: child.rank)
        for index, child in enumerate(children_sorted):
            child_copy = _copy_node_with_rank(child, rank=index)
            dst.children.append(child_copy)
            stack.append((child, child_copy))
            
    return root_copy


def keep_only_after_node(
    root: VariationNode, target: VariationNode
) -> VariationNode:
    """
    Create a new tree containing only the target node and everything after it.

    Args:
        root: Root of the variation tree
        target: Target node to start from

    Returns:
        Deep copy of target's subtree

    Example:
        If target is move 5 in a 10-move game, returns a tree
        with move 5 as root and moves 6-10 as children.
    """
    return copy_tree(target)


def remove_comments(node: VariationNode) -> VariationNode:
    """
    Create a copy of the tree with all comments removed.
    Iterative implementation.

    Args:
        node: Root node

    Returns:
        New tree without comments
    """
    root_copy = VariationNode(
        move_number=node.move_number,
        color=node.color,
        san=node.san,
        uci=node.uci,
        fen=node.fen,
        nag=node.nag,
        comment=None,  # Remove comment
        rank=node.rank,
    )
    
    stack = [(node, root_copy)]
    while stack:
        src, dst = stack.pop()
        for child in src.children:
            child_copy = VariationNode(
                move_number=child.move_number,
                color=child.color,
                san=child.san,
                uci=child.uci,
                fen=child.fen,
                nag=child.nag,
                comment=None,
                rank=child.rank,
            )
            dst.children.append(child_copy)
            stack.append((child, child_copy))

    return root_copy


def extract_mainline(node: VariationNode) -> VariationNode:
    """
    Create a new tree containing only the main line (rank=0 moves).
    Iterative implementation.

    Args:
        node: Root node

    Returns:
        New tree with only main line moves
    """
    root_copy = VariationNode(
        move_number=node.move_number,
        color=node.color,
        san=node.san,
        uci=node.uci,
        fen=node.fen,
        nag=node.nag,
        comment=node.comment,
        rank=0,
    )
    
    # Only follow rank=0 children
    current_src = node
    current_dst = root_copy
    
    while True:
        main_child = next((c for c in current_src.children if c.rank == 0), None)
        if not main_child:
            break
            
        child_copy = VariationNode(
            move_number=main_child.move_number,
            color=main_child.color,
            san=main_child.san,
            uci=main_child.uci,
            fen=main_child.fen,
            nag=main_child.nag,
            comment=main_child.comment,
            rank=0,
        )
        current_dst.children.append(child_copy)
        
        current_src = main_child
        current_dst = child_copy

    return root_copy
