from typing import Dict, Tuple
import chess
from backend.core.real_pgn.models import NodeTree

# From stage1c.md: PGN-Implementaion

def apply_move(parent_fen: str, move_str: str) -> Tuple[str, int, int]:
    """
    Applies a single move (SAN or UCI) to a FEN, validates it, and returns the new state.
    
    Returns:
        A tuple containing (new_fen, new_ply, new_move_number).
    """
    board = chess.Board(parent_fen)
    try:
        # Try parsing as SAN first, as it's more common in PGN context
        move = board.parse_san(move_str)
    except ValueError:
        try:
            # Fall back to UCI
            move = board.parse_uci(move_str)
        except ValueError:
            raise ValueError(f"Invalid move '{move_str}' for FEN '{parent_fen}'")

    board.push(move)
    
    new_fen = board.fen()
    new_ply = board.ply
    # fullmove_number is only incremented after Black's move
    new_move_number = board.fullmove_number
    
    return new_fen, new_ply, new_move_number


def build_fen_index(tree: NodeTree) -> Dict[str, str]:
    """
    Generates a dictionary mapping each node_id to its calculated FEN
    by traversing the NodeTree.
    """
    if not tree.root_id:
        return {}
    
    fen_index = {}
    root_node = tree.nodes[tree.root_id]
    start_fen = root_node.fen
    
    fen_index[tree.root_id] = start_fen
    
    _calculate_fen_recursive(tree, tree.root_id, start_fen, fen_index)
    
    return fen_index

def _calculate_fen_recursive(tree: NodeTree, node_id: str, current_fen: str, fen_index: Dict[str, str]):
    """
    Helper to recursively traverse the tree and calculate FENs.
    """
    node = tree.nodes[node_id]
    
    # Traverse main line
    if node.main_child:
        child_node = tree.nodes[node.main_child]
        board = chess.Board(current_fen)
        board.push_san(child_node.san)
        child_fen = board.fen()
        fen_index[child_node.node_id] = child_fen
        _calculate_fen_recursive(tree, child_node.node_id, child_fen, fen_index)

    # Traverse variations
    for var_id in node.variations:
        var_node = tree.nodes[var_id]
        board = chess.Board(current_fen)
        board.push_san(var_node.san)
        var_fen = board.fen()
        fen_index[var_node.node_id] = var_fen
        _calculate_fen_recursive(tree, var_node.node_id, var_fen, fen_index)

