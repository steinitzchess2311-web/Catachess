"""
Export PGN with variations but without comments.

This export mode:
- Keeps all variations (mainline and alternatives)
- Removes all text comments
- Keeps NAG annotations (!!, !?, ?, !, etc.)
- Useful for sharing games without giving away analysis
"""

from workspace.pgn.cleaner.variation_pruner import remove_comments
from workspace.pgn.serializer.to_pgn import tree_to_pgn, tree_to_movetext
from workspace.pgn.serializer.to_tree import VariationNode


def export_no_comment_pgn(
    root: VariationNode,
    headers: dict[str, str] | None = None,
    include_headers: bool = True,
) -> str:
    """
    Export PGN with all variations but no comments.

    Args:
        root: Root of the variation tree
        headers: Optional PGN headers
        include_headers: Whether to include headers in output

    Returns:
        PGN text without comments

    Example:
        >>> # Original PGN with comments:
        >>> # 1. e4 { King's pawn } e5 2. Nf3 { Developing } Nc6
        >>>
        >>> pgn = export_no_comment_pgn(root)
        >>> # Result:
        >>> # 1. e4 e5 2. Nf3 Nc6
    """
    # Remove comments from tree
    cleaned_tree = remove_comments(root)

    # Generate PGN
    if include_headers:
        resolved_headers = headers or getattr(root, "headers", None)
        return tree_to_pgn(cleaned_tree, headers=resolved_headers)
    else:
        return tree_to_movetext(cleaned_tree)


def export_no_comment_pgn_to_clipboard(root: VariationNode) -> str:
    """
    Export PGN without comments for clipboard (no headers).

    Args:
        root: Root of the variation tree

    Returns:
        PGN movetext without comments

    Example:
        >>> movetext = export_no_comment_pgn_to_clipboard(root)
        >>> # Can be pasted into chess software
    """
    return export_no_comment_pgn(root, include_headers=False)


def export_no_comment_with_nags(
    root: VariationNode,
    headers: dict[str, str] | None = None,
) -> str:
    """
    Export PGN without text comments but keeping NAG symbols.

    This is the same as export_no_comment_pgn (NAGs are kept by default),
    but makes the intent explicit.

    Args:
        root: Root of the variation tree
        headers: Optional PGN headers

    Returns:
        PGN text with NAGs but no text comments

    Example:
        >>> # Original:
        >>> # 1. e4 { Excellent } !! e5 { Typical response } ?!
        >>>
        >>> pgn = export_no_comment_with_nags(root)
        >>> # Result:
        >>> # 1. e4 !! e5 ?!
    """
    return export_no_comment_pgn(root, headers=headers, include_headers=True)
