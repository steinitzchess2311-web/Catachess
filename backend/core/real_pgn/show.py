from typing import List, Dict, Any
from backend.core.real_pgn.models import NodeTree, PgnNode

# From stage1b.md: PGN-Implementaion

def build_show(tree: NodeTree) -> Dict[str, Any]:
    """
    Generates a ShowDTO dictionary from a NodeTree, suitable for frontend rendering.
    """
    
    # 1. Headers array
    headers = [{"name": key, "value": value} for key, value in tree.meta.headers.items()]
    
    # 2. Nodes dict (already in the right format in tree.nodes)
    nodes_dict = {nid: node.__dict__ for nid, node in tree.nodes.items()}

    # 3. Render token stream
    render_tokens = []
    if tree.root_id:
        _build_tokens_recursive(tree, tree.root_id, render_tokens, is_mainline=True)
        
    return {
        "headers": headers,
        "nodes": nodes_dict,
        "render_tokens": render_tokens
    }

def _build_tokens_recursive(tree: NodeTree, node_id: str, tokens: List[Dict[str, Any]], is_mainline: bool):
    """
    Recursively builds the render token stream.
    """
    node = tree.nodes.get(node_id)
    if not node:
        return

    # Skip printing the root node itself, just start with its main line
    if node.san == "<root>":
        if node.variations:
            _build_tokens_recursive(tree, node.variations[0], tokens, is_mainline=True)
        return

    # Add move token
    tokens.append({"type": "move", "node_id": node.node_id, "san": node.san})

    # Add comment token if it exists
    if node.comment_after:
        tokens.append({"type": "comment", "text": node.comment_after})

    # Process side variations first
    if len(node.variations) > 1:
        for var_node_id in node.variations[1:]:
            tokens.append({"type": "variation_start"})
            _build_tokens_recursive(tree, var_node_id, tokens, is_mainline=False)
            tokens.append({"type": "variation_end"})
    
    # Then continue with the main line
    if node.variations:
        _build_tokens_recursive(tree, node.variations[0], tokens, is_mainline)
