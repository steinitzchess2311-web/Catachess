"""
Convert PGN text to variation tree structure.

This module parses PGN movetext (including variations in parentheses)
and constructs a tree representation suitable for database storage.

DEPRECATED: Use backend.core.real_pgn for new PGN processing.
"""

from dataclasses import dataclass, field
from io import StringIO

import chess
import chess.pgn
import re


@dataclass
class VariationNode:
    """
    Represents a single move node in the variation tree.

    Attributes:
        move_number: Full move number (1, 2, 3...)
        color: 'white' or 'black'
        san: Standard Algebraic Notation (e.g., 'e4', 'Nf3')
        uci: Universal Chess Interface notation (e.g., 'e2e4', 'g1f3')
        fen: FEN position after this move
        nag: Numeric Annotation Glyph (e.g., '!', '?', '!!', '??')
        comment: Text comment for this move
        children: List of child variations (main line + alternatives)
        rank: Rank among siblings (0=main, 1=first alternative, etc.)
    """

    move_number: int
    color: str  # 'white' or 'black'
    san: str
    uci: str
    fen: str
    nag: str | None = None
    comment: str | None = None
    children: list["VariationNode"] = field(default_factory=list)
    rank: int = 0
    headers: dict[str, str] | None = None

    def __repr__(self) -> str:
        """String representation."""
        nag_str = f" {self.nag}" if self.nag else ""
        return f"<VariationNode({self.san}{nag_str}, rank={self.rank})>"


def _nag_to_symbol(nag: int) -> str | None:
    """
    Convert chess.pgn NAG code to symbol.

    Args:
        nag: NAG code

    Returns:
        Symbol string or None
    """
    nag_map = {
        1: "!",   # Good move
        2: "?",   # Mistake
        3: "!!",  # Brilliant move
        4: "??",  # Blunder
        5: "!?",  # Interesting move
        6: "?!",  # Dubious move
    }
    return nag_map.get(nag)


def _parse_node(
    node: chess.pgn.GameNode,
    parent_board: chess.Board,
    rank: int = 0,
) -> VariationNode:
    """
    Recursively parse a chess.pgn node into a VariationNode,
    but use iteration for the main line to avoid stack overflow.

    Args:
        node: chess.pgn node
        parent_board: Board position before this move
        rank: Rank among siblings (0=main line, 1+=alternatives)

    Returns:
        VariationNode representing this move and its children
    """
    current_pgn_node = node
    # Make a copy of the board to avoid modifying parent
    current_board = parent_board.copy()
    current_rank = rank

    first_var_node: VariationNode | None = None
    previous_var_node: VariationNode | None = None

    while True:
        # Get move information
        move = current_pgn_node.move
        if move is None:
            break

        san = current_board.san(move)
        uci = move.uci()
        move_number = current_board.fullmove_number
        color = "white" if current_board.turn == chess.WHITE else "black"

        # Apply move to get new position
        current_board.push(move)
        fen = current_board.fen()

        # Get NAG (annotation glyph)
        nag = None
        if current_pgn_node.nags:
            # Take first NAG if multiple exist
            nag_code = list(current_pgn_node.nags)[0]
            nag = _nag_to_symbol(nag_code)

        # Get comment
        comment = current_pgn_node.comment.strip() if current_pgn_node.comment else None

        # Create node
        var_node = VariationNode(
            move_number=move_number,
            color=color,
            san=san,
            uci=uci,
            fen=fen,
            nag=nag,
            comment=comment,
            rank=current_rank,
        )

        if first_var_node is None:
            first_var_node = var_node

        if previous_var_node:
            previous_var_node.children.append(var_node)

        # Parse child variations
        if not current_pgn_node.is_end():
            # Handle alternatives (rank > 0)
            # node.variations contains all branches including main line
            # variations[0] is the main line, variations[1:] are alternatives
            if len(current_pgn_node.variations) > 1:
                for child_rank, variation in enumerate(current_pgn_node.variations[1:], start=1):
                    child_node = _parse_node(variation, current_board, rank=child_rank)
                    var_node.children.append(child_node)
            
            # Handle main line (rank 0) iteratively
            if current_pgn_node.variations:
                current_pgn_node = current_pgn_node.variations[0]
                current_rank = 0
                previous_var_node = var_node
            else:
                break
        else:
            break

    return first_var_node


def pgn_to_tree(pgn_text: str) -> VariationNode | None:
    """
    Convert PGN text to a variation tree.

    Args:
        pgn_text: PGN format text including headers and moves

    Returns:
        Root VariationNode representing the first move, or None if no moves

    Example:
        >>> pgn = '''
        ... [Event "Test"]
        ... [White "Player 1"]
        ... [Black "Player 2"]
        ...
        ... 1. e4 e5 (1...c5 2. Nf3) 2. Nf3 Nc6
        ... '''
        >>> tree = pgn_to_tree(pgn)
        >>> tree.san
        'e4'
        >>> len(tree.children)
        1
        >>> tree.children[0].san
        'e5'
        >>> len(tree.children[0].children)
        2  # Main line (Nf3) and alternative (c5)
    """
    # Normalize black-move notation (e.g., "1... c5" -> "1...c5") for parser tolerance.
    normalized = re.sub(r"(\\d+)\\.\\.\\.\\s+", r"\\1...", pgn_text)

    # Parse PGN
    pgn_io = StringIO(normalized)
    game = chess.pgn.read_game(pgn_io)

    if game is None:
        return None

    # Get first move
    if game.is_end():
        return None

    # Start from initial position
    board = game.board()

    # Parse the first move and its children recursively
    root = _parse_node(game.next(), board, rank=0)
    root.headers = dict(game.headers)

    # Include alternative first moves as variations on the root
    if len(game.variations) > 1:
        for alt_rank, variation in enumerate(game.variations[1:], start=1):
            alt_node = _parse_node(variation, board, rank=alt_rank)
            root.children.append(alt_node)
        root.children.sort(key=lambda child: child.rank)

    return root


def flatten_tree(root: VariationNode | None) -> list[VariationNode]:
    """
    Flatten variation tree to a list (breadth-first traversal).

    Args:
        root: Root variation node

    Returns:
        List of all variation nodes in tree

    Example:
        >>> tree = pgn_to_tree(pgn_text)
        >>> nodes = flatten_tree(tree)
        >>> len(nodes)
        5  # Total number of moves including variations
    """
    if root is None:
        return []

    result = []
    queue = [root]

    while queue:
        node = queue.pop(0)
        result.append(node)
        queue.extend(node.children)

    return result


def get_main_line(root: VariationNode | None) -> list[VariationNode]:
    """
    Extract the main line (rank=0 path) from a variation tree.

    Args:
        root: Root variation node

    Returns:
        List of nodes in the main line

    Example:
        >>> tree = pgn_to_tree(pgn_text)
        >>> main_line = get_main_line(tree)
        >>> [node.san for node in main_line]
        ['e4', 'e5', 'Nf3', 'Nc6']
    """
    if root is None:
        return []

    result = []
    current = root

    while current:
        result.append(current)
        # Find next main line node (rank=0)
        main_child = next(
            (child for child in current.children if child.rank == 0), None
        )
        current = main_child

    return result
