from typing import List, Dict, Any
from backend.core.real_pgn.models import NodeTree, PgnNode

# From stage1b.md: PGN-Implementaion

def build_show(tree: NodeTree) -> Dict[str, Any]:
    """
    Generates a ShowDTO dictionary from a NodeTree, suitable for frontend rendering.
    """
    
    # 1. Headers array with 'k' and 'v' keys
    headers = [{"k": key, "v": value} for key, value in tree.meta.headers.items()]
    
    # 2. Nodes dict (no change needed here)
    nodes_dict = {nid: node.__dict__ for nid, node in tree.nodes.items()}

    # 3. Render token stream
    render_stream = []
    if tree.root_id:
        _build_tokens_recursive(tree, tree.root_id, render_stream, is_variation_start=False)
        
    # 4. Other metadata
    root_fen = tree.nodes[tree.root_id].fen if tree.root_id else None

    return {
        "headers": headers,
        "nodes": nodes_dict,
        "render": render_stream,
        "root_fen": root_fen,
        "result": tree.meta.result
    }

def _build_tokens_recursive(tree: NodeTree, node_id: str, tokens: List[Dict[str, Any]], is_variation_start: bool):
    """
    Recursively builds the render token stream with the new DTO structure.
    """
    node = tree.nodes.get(node_id)
    if not node:
        return

    # Skip the root node, start recursion from its main child
    if node.san == "<root>":
        if node.main_child:
            _build_tokens_recursive(tree, node.main_child, tokens, is_variation_start=False)
        return

    # --- Label Generation ---
    label = ""
    is_black_move = node.ply % 2 == 0
    if node.ply % 2 == 1:  # White's move
        label = f"{node.move_number}."
    elif is_variation_start:  # Black's move starting a variation
        label = f"{node.move_number}..."
    
    if is_variation_start:
        label = f"({label}"

    # --- Token Generation ---
    
    # Add move token
    tokens.append({
        "t": "m",
        "node": node.node_id,
        "label": label,
        "san": node.san
    })

    # Add comment token if it exists
    if node.comment_after:
        tokens.append({"t": "c", "text": node.comment_after})

    # Process side variations
    for var_node_id in node.variations:
        tokens.append({"t": "v_start"})
        _build_tokens_recursive(tree, var_node_id, tokens, is_variation_start=True)
        tokens.append({"t": "v_end"})
    
    # Continue with the main line
    if node.main_child:
        _build_tokens_recursive(tree, node.main_child, tokens, is_variation_start=False)
