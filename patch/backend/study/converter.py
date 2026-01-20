from backend.core.real_pgn.models import NodeTree
from patch.backend.study.models import StudyTreeDTO, StudyNodeDTO, TreeMetaDTO

def convert_nodetree_to_dto(node_tree: NodeTree) -> StudyTreeDTO:
    """Convert backend NodeTree to patch StudyTreeDTO."""
    
    nodes = {}
    
    root_id = "root"
    nodes[root_id] = StudyNodeDTO(
        id=root_id,
        parentId=None,
        san="",
        children=[],
        comment=None,
        nags=[]
    )
    
    if node_tree.root_id:
        _traverse_and_map(node_tree, node_tree.root_id, root_id, nodes)
        nodes[root_id].children.append(node_tree.root_id)
        
    meta = TreeMetaDTO(result=node_tree.meta.result)
    
    return StudyTreeDTO(
        version="v1",
        rootId=root_id,
        nodes=nodes,
        meta=meta
    )

def _traverse_and_map(node_tree: NodeTree, current_id: str, parent_id: str, nodes: dict):
    """Recursively map nodes."""
    src_node = node_tree.nodes.get(current_id)
    if not src_node:
        return

    # Combine comments
    comment = src_node.comment_after or src_node.comment_before
    if src_node.comment_before and src_node.comment_after:
        comment = f"{src_node.comment_before} {src_node.comment_after}"

    dto_node = StudyNodeDTO(
        id=src_node.node_id,
        parentId=parent_id,
        san=src_node.san,
        children=[],
        comment=comment,
        nags=src_node.nags
    )
    
    # Handle children
    if src_node.main_child:
        dto_node.children.append(src_node.main_child)
        _traverse_and_map(node_tree, src_node.main_child, src_node.node_id, nodes)
        
    for var_id in src_node.variations:
        dto_node.children.append(var_id)
        _traverse_and_map(node_tree, var_id, src_node.node_id, nodes)
        
    nodes[src_node.node_id] = dto_node
