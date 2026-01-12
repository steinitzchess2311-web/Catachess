"""
Export raw PGN (mainline only).

This export mode:
- Keeps only the main line (rank=0 moves)
- Removes all alternative variations
- Keeps comments and NAGs from main line
- Simplest view of the game
"""

from workspace.pgn.cleaner.variation_pruner import extract_mainline
from workspace.pgn.serializer.to_pgn import tree_to_pgn, tree_to_movetext
from workspace.pgn.serializer.to_tree import VariationNode


def export_raw_pgn(
    root: VariationNode,
    headers: dict[str, str] | None = None,
    include_headers: bool = True,
) -> str:
    """
    Export only the main line (raw PGN).

    Args:
        root: Root of the variation tree
        headers: Optional PGN headers
        include_headers: Whether to include headers in output

    Returns:
        PGN text with mainline only

    Example:
        >>> # Original PGN with variations:
        >>> # 1. e4 (1. d4) e5 (1...c5) 2. Nf3 (2. Bc4) Nc6
        >>>
        >>> pgn = export_raw_pgn(root)
        >>> # Result:
        >>> # 1. e4 e5 2. Nf3 Nc6
    """
    # Extract mainline
    mainline_tree = extract_mainline(root)

    # Generate PGN
    if include_headers:
        resolved_headers = headers or getattr(root, "headers", None)
        return tree_to_pgn(mainline_tree, headers=resolved_headers)
    else:
        return tree_to_movetext(mainline_tree)


def export_raw_pgn_to_clipboard(root: VariationNode) -> str:
    """
    Export mainline PGN for clipboard (no headers).

    Args:
        root: Root of the variation tree

    Returns:
        PGN movetext with mainline only

    Example:
        >>> movetext = export_raw_pgn_to_clipboard(root)
        >>> # Simple mainline, ready to paste
    """
    return export_raw_pgn(root, include_headers=False)


def export_clean_mainline(
    root: VariationNode,
    headers: dict[str, str] | None = None,
) -> str:
    """
    Export clean mainline (no variations, no comments).

    Combines mainline extraction with comment removal.

    Args:
        root: Root of the variation tree
        headers: Optional PGN headers

    Returns:
        Clean PGN with only mainline moves, no comments

    Example:
        >>> # Original:
        >>> # 1. e4 { Great } (1. d4 { Also good }) e5 { Classic }
        >>>
        >>> pgn = export_clean_mainline(root)
        >>> # Result:
        >>> # 1. e4 e5
    """
    from workspace.pgn.cleaner.variation_pruner import remove_comments

    # Extract mainline and remove comments
    mainline = extract_mainline(root)
    clean = remove_comments(mainline)

    resolved_headers = headers or getattr(root, "headers", None)
    return tree_to_pgn(clean, headers=resolved_headers)
