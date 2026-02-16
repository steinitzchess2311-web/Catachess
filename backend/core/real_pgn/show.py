"""
⚠️⚠️⚠️ LEGACY CODE - USED BY OLD FRONTEND ONLY ⚠️⚠️⚠️

This module builds ShowDTO for the OLD frontend ShowDTO system.
The OLD frontend (frontend/ui/modules/study/) has been REPLACED by patch/.

Current system uses tree.json directly:
- Frontend: patch/sidebar/movetree.tsx
- Backend API: patch/backend/study/api.py
- Data format: StudyTreeDTO (patch/backend/study/models.py)
- Storage: R2 tree.json (chapters/{id}.tree.json)

This code is still used by:
- backend/modules/workspace/api/endpoints/studies.py:get_chapter_show()
  for backward compatibility with old frontend.

DO NOT USE for new features. Use patch/ system instead.
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
"""

from typing import List, Dict, Any
from backend.core.real_pgn.models import NodeTree, PgnNode

# From stage1b.md: PGN-Implementaion

def build_show(tree: NodeTree) -> Dict[str, Any]:
    """
    Generates a ShowDTO dictionary from a NodeTree, suitable for frontend rendering.
    """
    
    headers = [{"k": key, "v": value} for key, value in tree.meta.headers.items()]
    nodes_dict = {nid: node.__dict__ for nid, node in tree.nodes.items()}
    render_stream = []
    
    if tree.root_id:
        _build_tokens_recursive(tree, tree.root_id, render_stream, is_variation_start=False)
        
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



    if node.san == "<root>":

        if node.main_child:

            _build_tokens_recursive(tree, node.main_child, tokens, is_variation_start=False)

        return



    # --- Label Generation ---

    label = ""

    is_black_move = node.ply % 2 == 0

    parent_is_root = tree.nodes.get(node.parent_id).san == "<root>" if node.parent_id else False



    if not is_black_move:  # White's move

        label = f"{node.move_number}."

    elif is_variation_start or parent_is_root:  # Black move needing a number

        label = f"{node.move_number}..."

    

    # Add parenthesis prefix if this move starts a variation

    if is_variation_start:

        label = f"({label}"



    # --- Token Generation ---

    if node.comment_before:
        tokens.append({"t": "comment", "node": node.node_id, "text": node.comment_before})

    tokens.append({

        "t": "move",

        "node": node.node_id,

        "label": label,

        "san": node.san

    })



    if node.comment_after:

        tokens.append({"t": "comment", "node": node.node_id, "text": node.comment_after})



    for var_node_id in node.variations:

        # Add 'from' field to variation_start token

        tokens.append({"t": "variation_start", "from": node.node_id})

        _build_tokens_recursive(tree, var_node_id, tokens, is_variation_start=True)

        tokens.append({"t": "variation_end"})

    

    if node.main_child:

        _build_tokens_recursive(tree, node.main_child, tokens, is_variation_start=False)

