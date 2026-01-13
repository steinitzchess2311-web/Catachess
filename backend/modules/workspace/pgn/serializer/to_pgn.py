"""
Convert variation tree structure to PGN text.

This module takes a tree representation of moves and variations
and generates standard PGN movetext format.
"""

from workspace.pgn.serializer.to_tree import VariationNode


def _format_move_with_number(
    node: VariationNode, prev_color: str | None
) -> str:
    """
    Format a move with its move number if needed.

    Args:
        node: Variation node
        prev_color: Color of previous move ('white', 'black', or None)

    Returns:
        Formatted move string (e.g., '1. e4' or '1...e5' or 'Nf3')
    """
    san = node.san

    # Add NAG if present
    if node.nag:
        san = f"{san} {node.nag}"

    # Determine if we need to show move number
    if node.color == "white":
        # White move always shows number
        return f"{node.move_number}. {san}"
    else:
        # Black move shows number only if:
        # 1. It's the first move (prev_color is None)
        # 2. Previous move was also black (starting variation mid-move)
        if prev_color is None or prev_color == "black":
            return f"{node.move_number}...{san}"
        else:
            return san


def _serialize_node(
    node: VariationNode,
    prev_color: str | None = None,
    is_variation: bool = False,
) -> str:
    """
    Recursively serialize a variation node to PGN text.
    Iterative for main line to prevent recursion depth exceeded.

    Args:
        node: Variation node to serialize
        prev_color: Color of previous move
        is_variation: True if this is an alternative variation (unused but kept for API compatibility)

    Returns:
        PGN movetext string
    """
    full_result = []
    
    current_node: VariationNode | None = node
    current_prev_color = prev_color
    
    while current_node:
        # Format current move
        move_str = _format_move_with_number(current_node, current_prev_color)
        full_result.append(move_str)

        # Add comment if present
        if current_node.comment:
            full_result.append(f"{{ {current_node.comment} }}")

        # Process children
        if current_node.children:
            # Separate main line (rank=0) from alternatives
            main_child = next(
                (child for child in current_node.children if child.rank == 0), None
            )
            alternatives = [
                child for child in current_node.children if child.rank > 0
            ]

            # Serialize alternatives first (they appear before main continuation)
            for alt in sorted(alternatives, key=lambda x: x.rank):
                # Pass None as prev_color so variation starts with full move number
                # Recursion is safe here as variation depth is typically low
                alt_text = _serialize_node(alt, None, is_variation=True)
                full_result.append(f"( {alt_text} )")

            # Proceed to main line (iterative)
            if main_child:
                current_prev_color = current_node.color
                current_node = main_child
            else:
                current_node = None
        else:
            current_node = None

    return " ".join(full_result)


def tree_to_pgn(
    root: VariationNode | None,
    headers: dict[str, str] | None = None,
    result: str | None = None,
) -> str:
    """
    Convert variation tree to complete PGN text.

    Args:
        root: Root variation node (first move)
        headers: Optional PGN headers (Event, Site, Date, etc.)
        result: Optional game result ('1-0', '0-1', '1/2-1/2', '*')

    Returns:
        Complete PGN text including headers and moves

    Example:
        >>> tree = VariationNode(
        ...     move_number=1,
        ...     color='white',
        ...     san='e4',
        ...     uci='e2e4',
        ...     fen='rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
        ... )
        >>> headers = {
        ...     'Event': 'Test Game',
        ...     'White': 'Player 1',
        ...     'Black': 'Player 2',
        ...     'Result': '*'
        ... }
        >>> pgn = tree_to_pgn(tree, headers)
        >>> print(pgn)
        [Event "Test Game"]
        [White "Player 1"]
        [Black "Player 2"]
        [Result "*"]
        <BLANKLINE>
        1. e4 *
    """
    lines = []

    # Add headers
    if headers:
        # Standard header order
        header_order = [
            "Event",
            "Site",
            "Date",
            "Round",
            "White",
            "Black",
            "Result",
        ]

        # Add ordered headers first
        for key in header_order:
            if key in headers:
                lines.append(f'[{key} "{headers[key]}"]')

        # Add remaining headers
        for key, value in headers.items():
            if key not in header_order:
                lines.append(f'[{key} "{value}"]')

        # Blank line after headers
        lines.append("")

    # Add movetext
    if root:
        movetext = _serialize_node(root)
        lines.append(movetext)

    # Add result
    if result:
        lines.append(result)
    elif headers and "Result" in headers:
        lines.append(headers["Result"])
    else:
        lines.append("*")

    return "\n".join(lines)


def tree_to_movetext(root: VariationNode | None) -> str:
    """
    Convert variation tree to PGN movetext only (no headers).

    Args:
        root: Root variation node

    Returns:
        PGN movetext string

    Example:
        >>> tree = VariationNode(...)
        >>> movetext = tree_to_movetext(tree)
        >>> print(movetext)
        1. e4 e5 2. Nf3 Nc6
    """
    if root is None:
        return ""

    return _serialize_node(root)


def format_variation_path(nodes: list[VariationNode]) -> str:
    """
    Format a list of variation nodes as a PGN line.

    Args:
        nodes: List of variation nodes in order

    Returns:
        Formatted PGN string

    Example:
        >>> nodes = [node1, node2, node3]
        >>> path = format_variation_path(nodes)
        >>> print(path)
        1. e4 e5 2. Nf3
    """
    if not nodes:
        return ""

    result = []
    prev_color = None

    for node in nodes:
        move_str = _format_move_with_number(node, prev_color)
        result.append(move_str)
        prev_color = node.color

    return " ".join(result)
