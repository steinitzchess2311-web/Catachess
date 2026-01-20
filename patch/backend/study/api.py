import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StudyTreeDTO, TreeResponse
from modules.workspace.storage.r2_client import R2Client, create_r2_client_from_env
from modules.workspace.storage.keys import R2Keys
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.session import get_session

router = APIRouter(prefix="/study-patch", tags=["study-patch"])
logger = logging.getLogger(__name__)

def _validate_tree_structure(tree: StudyTreeDTO) -> list[str]:
    errors: list[str] = []

    if tree.version != "v1":
        errors.append(f'Invalid version: expected "v1", got "{tree.version}"')

    if not tree.rootId:
        errors.append("Missing rootId")

    if not tree.nodes:
        errors.append("Missing nodes")
        return errors

    if tree.rootId not in tree.nodes:
        errors.append(f'Root node "{tree.rootId}" not found in nodes')
    else:
        root = tree.nodes[tree.rootId]
        if root.parentId is not None:
            errors.append("Root node must have parentId = null")
        if root.san != "":
            errors.append("Root node must have empty san")

    for node_id, node in tree.nodes.items():
        if node.id != node_id:
            errors.append(f'Node id mismatch: key "{node_id}" != node.id "{node.id}"')

        if node_id != tree.rootId and node.parentId is None:
            errors.append(f'Node "{node_id}" missing parentId')
        if node.parentId is not None and node.parentId not in tree.nodes:
            errors.append(f'Node "{node_id}" has invalid parentId "{node.parentId}"')

        for child_id in node.children:
            if child_id not in tree.nodes:
                errors.append(f'Node "{node_id}" has invalid child "{child_id}"')
            else:
                child = tree.nodes[child_id]
                if child.parentId != node_id:
                    errors.append(
                        f'Node "{node_id}" child "{child_id}" parentId mismatch "{child.parentId}"'
                    )

    return errors

async def get_r2_client() -> R2Client:
    return create_r2_client_from_env()

async def get_study_repo(session: AsyncSession = Depends(get_session)) -> StudyRepository:
    return StudyRepository(session)

@router.get("/chapter/{chapter_id}/tree", response_model=TreeResponse)
async def get_chapter_tree(
    chapter_id: str,
    r2_client: R2Client = Depends(get_r2_client)
):
    """Get the tree.json for a chapter from R2."""
    key = R2Keys.chapter_tree_json(chapter_id)
    try:
        if not r2_client.exists(key):
            return TreeResponse(success=False, error="Tree not found")
        
        content = r2_client.download_json(key)
        tree_data = json.loads(content)
        return TreeResponse(success=True, tree=StudyTreeDTO(**tree_data))
    except Exception as e:
        logger.error(f"Failed to get tree for chapter {chapter_id}: {e}")
        return TreeResponse(success=False, error=str(e))

@router.put("/chapter/{chapter_id}/tree", response_model=TreeResponse)
async def put_chapter_tree(
    chapter_id: str,
    tree: StudyTreeDTO,
    r2_client: R2Client = Depends(get_r2_client)
):
    """Save the tree.json for a chapter to R2."""
    validation_errors = _validate_tree_structure(tree)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tree: " + "; ".join(validation_errors),
        )

    # Note: StudyTreeDTO and StudyNodeDTO do not include FEN fields,
    # ensuring no FEN is persisted in the tree JSON.

    key = R2Keys.chapter_tree_json(chapter_id)
    try:
        content = tree.model_dump_json()
        r2_client.upload_json(key, content)
        logger.info(f"Tree saved for chapter {chapter_id} (size: {len(content)} bytes)")
        return TreeResponse(success=True)
    except Exception as e:
        logger.error(f"Failed to save tree for chapter {chapter_id}: {e}")
        return TreeResponse(success=False, error=str(e))

@router.get("/chapter/{chapter_id}/pgn-export")
async def export_chapter_pgn(
    chapter_id: str,
    r2_client: R2Client = Depends(get_r2_client),
    study_repo: StudyRepository = Depends(get_study_repo)
):
    """Export the tree.json as a PGN string."""
    key = R2Keys.chapter_tree_json(chapter_id)
    try:
        logger.info(f"Exporting PGN for chapter {chapter_id}...")
        if not r2_client.exists(key):
            raise HTTPException(status_code=404, detail="Tree not found")
        
        content = r2_client.download_json(key)
        tree_data = json.loads(content)
        tree = StudyTreeDTO(**tree_data)
        
        chapter = await study_repo.get_chapter_by_id(chapter_id)
        title = chapter.title if chapter else "Chapter"
        
        pgn = _tree_to_pgn(tree, title)
        logger.info(f"PGN export successful for chapter {chapter_id} (length: {len(pgn)})")
        return {"success": True, "pgn": pgn}

def _tree_to_pgn(tree: StudyTreeDTO, chapter) -> str:
    """Helper to convert StudyTreeDTO to PGN string."""
    event = getattr(chapter, "event", None) or getattr(chapter, "title", None) or "Chapter"
    white = getattr(chapter, "white", None) or "?"
    black = getattr(chapter, "black", None) or "?"
    date = getattr(chapter, "date", None) or "????.??.??"
    result = tree.meta.result or getattr(chapter, "result", None) or "*"

    # Headers come from chapter metadata; tree does not store headers.
    headers = {
        "Event": event,
        "Site": "?",
        "Date": date,
        "Round": "?",
        "White": white,
        "Black": black,
        "Result": result,
    }
    
    header_str = "\n".join([f'[{k} "{v}"]' for k, v in headers.items()])
    
    def build_text(node_id: str, move_num: int, is_white: bool, force_num: bool = False) -> str:
        node = tree.nodes.get(node_id)
        if not node or not node.san: return ""
        
        parts = []
        if is_white or force_num:
            parts.append(f"{move_num}.{'..' if not is_white else ''} {node.san}")
        else:
            parts.append(node.san)
            
        if node.comment:
            parts.append(f"{{{node.comment}}}")
        
        # Side variations
        if len(node.children) > 1:
            for i in range(1, len(node.children)):
                # Variations start with the same move number/color as this node
                var_text = build_text(node.children[i], move_num, is_white, force_num=True)
                if var_text:
                    parts.append(f"({var_text})")
        
        # Continuation
        if node.children:
            next_is_white = not is_white
            next_move_num = move_num if is_white else move_num + 1
            # If we had variations or comments, we MUST force the number for the continuation if it's black's move
            # or if it's white's move (which already has it).
            need_force = len(node.children) > 1 or node.comment is not None
            rest = build_text(node.children[0], next_move_num, next_is_white, force_num=need_force)
            if rest:
                parts.append(rest)
            
        return " ".join(parts)

    root_node = tree.nodes.get(tree.rootId)
    movetext = ""
    if root_node and root_node.children:
        movetext = build_text(root_node.children[0], 1, True)
        # Handle root-level variations (rare but possible in PGN)
        if len(root_node.children) > 1:
            for i in range(1, len(root_node.children)):
                var_text = build_text(root_node.children[i], 1, True)
                if var_text:
                    movetext += f" ({var_text})"
    else:
        movetext = "*"

    return f"{header_str}\n\n{movetext} {headers['Result']}"
