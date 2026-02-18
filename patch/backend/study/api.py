import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StudyTreeDTO, TreeResponse
from modules.workspace.storage.r2_client import R2Client, create_r2_client_from_env
from modules.workspace.storage.keys import R2Keys
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.session import get_session

router = APIRouter(prefix="/study-patch", tags=["study-patch"])
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("[STUDY PATCH API] Router initialized with prefix: /study-patch")
logger.info("[STUDY PATCH API] This module provides PGN export endpoints")
logger.info("=" * 80)

def _validate_tree_structure(tree: StudyTreeDTO) -> list[str]:
    errors: list[str] = []

    SUPPORTED_VERSIONS = {"v1", "v2"}
    if tree.version not in SUPPORTED_VERSIONS:
        errors.append(f'Invalid version: expected one of {sorted(SUPPORTED_VERSIONS)}, got "{tree.version}"')

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
    r2_client: R2Client = Depends(get_r2_client),
    study_repo: StudyRepository = Depends(get_study_repo)
):
    """Get the tree.json for a chapter from R2."""
    key = R2Keys.chapter_tree_json(chapter_id)
    try:
        # Get chapter metadata (including starting_fen)
        chapter = await study_repo.get_chapter_by_id(chapter_id)
        if not chapter:
            return TreeResponse(success=False, error="Chapter not found")

        if not r2_client.exists(key):
            return TreeResponse(success=False, error="Tree not found")

        content = r2_client.download_json(key)
        tree_data = json.loads(content)
        return TreeResponse(
            success=True,
            tree=StudyTreeDTO(**tree_data),
            starting_fen=chapter.starting_fen  # Include starting_fen from database
        )
    except Exception as e:
        logger.error(f"Failed to get tree for chapter {chapter_id}: {e}")
        return TreeResponse(success=False, error=str(e))

@router.put("/chapter/{chapter_id}/tree", response_model=TreeResponse)
async def put_chapter_tree(
    chapter_id: str,
    tree: StudyTreeDTO,
    request: Request,
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
        client_hash = request.headers.get("X-Tree-Hash")
        content = tree.model_dump_json()
        r2_client.upload_json(key, content)
        logger.info(f"Tree saved for chapter {chapter_id} (size: {len(content)} bytes)")
        if client_hash:
            logger.info(f"Tree hash received for chapter {chapter_id}: {client_hash}")
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
    logger.info("=" * 60)
    logger.info(f"[EXPORT CHAPTER PGN] ENDPOINT CALLED")
    logger.info(f"[EXPORT CHAPTER PGN] Chapter ID: {chapter_id}")
    logger.info("=" * 60)

    key = R2Keys.chapter_tree_json(chapter_id)
    logger.info(f"[EXPORT CHAPTER PGN] R2 Key: {key}")

    try:
        logger.info(f"[EXPORT CHAPTER PGN] Checking if R2 key exists...")
        exists = r2_client.exists(key)
        logger.info(f"[EXPORT CHAPTER PGN] R2 key exists: {exists}")

        if not exists:
            logger.error(f"[EXPORT CHAPTER PGN] Tree not found for chapter {chapter_id}")
            raise HTTPException(status_code=404, detail="Tree not found")

        logger.info(f"[EXPORT CHAPTER PGN] Downloading tree from R2...")
        content = r2_client.download_json(key)
        logger.info(f"[EXPORT CHAPTER PGN] Downloaded content length: {len(content)}")

        tree_data = json.loads(content)
        logger.info(f"[EXPORT CHAPTER PGN] Parsed tree data, nodes count: {len(tree_data.get('nodes', {}))}")

        tree = StudyTreeDTO(**tree_data)
        logger.info(f"[EXPORT CHAPTER PGN] Created StudyTreeDTO")

        logger.info(f"[EXPORT CHAPTER PGN] Fetching chapter metadata from DB...")
        chapter = await study_repo.get_chapter_by_id(chapter_id)
        logger.info(f"[EXPORT CHAPTER PGN] Chapter metadata: {chapter}")

        # Get study info for filename
        study = await study_repo.get_study_by_id(chapter.study_id)
        study_title = getattr(study, 'title', None) or 'Study'
        chapter_title = getattr(chapter, 'title', None) or 'Chapter'

        logger.info(f"[EXPORT CHAPTER PGN] Converting tree to PGN...")
        pgn = _tree_to_pgn(tree, chapter)
        logger.info(f"[EXPORT CHAPTER PGN] PGN generated successfully")
        logger.info(f"[EXPORT CHAPTER PGN] PGN length: {len(pgn)}")
        logger.info(f"[EXPORT CHAPTER PGN] PGN preview (first 200 chars): {pgn[:200]}")

        # Generate safe filename
        safe_study = _sanitize_filename(study_title)
        safe_chapter = _sanitize_filename(chapter_title)
        filename = f"{safe_study} - {safe_chapter}.pgn"
        logger.info(f"[EXPORT CHAPTER PGN] Generated filename: {filename}")

        result = {"success": True, "pgn": pgn, "filename": filename}
        logger.info(f"[EXPORT CHAPTER PGN] Returning success response")
        logger.info("=" * 60)
        return result
    except HTTPException as he:
        logger.error(f"[EXPORT CHAPTER PGN] HTTPException: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"[EXPORT CHAPTER PGN] Unexpected error: {type(e).__name__}")
        logger.error(f"[EXPORT CHAPTER PGN] Error message: {str(e)}")
        logger.error(f"[EXPORT CHAPTER PGN] Error details:", exc_info=True)
        return {"success": False, "error": str(e)}

@router.get("/study/{study_id}/pgn-export")
async def export_study_pgn(
    study_id: str,
    r2_client: R2Client = Depends(get_r2_client),
    study_repo: StudyRepository = Depends(get_study_repo)
):
    """Export all chapters in a study as concatenated PGN."""
    logger.info("=" * 60)
    logger.info(f"[EXPORT STUDY PGN] ENDPOINT CALLED")
    logger.info(f"[EXPORT STUDY PGN] Study ID: {study_id}")
    logger.info("=" * 60)

    try:
        logger.info(f"[EXPORT STUDY PGN] Fetching study metadata...")
        study = await study_repo.get_study_by_id(study_id)
        study_title = getattr(study, 'title', None) or 'Study'
        logger.info(f"[EXPORT STUDY PGN] Study title: {study_title}")

        logger.info(f"[EXPORT STUDY PGN] Fetching chapters for study...")
        chapters = await study_repo.get_chapters_for_study(study_id, order_by_order=True)
        logger.info(f"[EXPORT STUDY PGN] Found {len(chapters) if chapters else 0} chapters")

        if not chapters:
            logger.info(f"[EXPORT STUDY PGN] No chapters found, returning empty PGN")
            safe_title = _sanitize_filename(study_title)
            filename = f"{safe_title}.pgn"
            return {"success": True, "pgn": "", "filename": filename}

        pgn_blocks: list[str] = []
        for idx, chapter in enumerate(chapters):
            logger.info(f"[EXPORT STUDY PGN] Processing chapter {idx + 1}/{len(chapters)}: {chapter.id}")
            key = R2Keys.chapter_tree_json(chapter.id)
            logger.info(f"[EXPORT STUDY PGN] R2 Key: {key}")

            exists = r2_client.exists(key)
            logger.info(f"[EXPORT STUDY PGN] R2 key exists: {exists}")

            if not exists:
                logger.error(f"[EXPORT STUDY PGN] Tree not found for chapter {chapter.id}")
                raise HTTPException(status_code=404, detail=f"Tree not found for chapter {chapter.id}")

            content = r2_client.download_json(key)
            tree_data = json.loads(content)
            tree = StudyTreeDTO(**tree_data)
            pgn = _tree_to_pgn(tree, chapter)
            logger.info(f"[EXPORT STUDY PGN] Chapter {idx + 1} PGN length: {len(pgn)}")
            pgn_blocks.append(pgn)

        combined_pgn = "\n\n".join(pgn_blocks)
        logger.info(f"[EXPORT STUDY PGN] Combined PGN length: {len(combined_pgn)}")

        # Generate safe filename
        safe_title = _sanitize_filename(study_title)
        filename = f"{safe_title}.pgn"
        logger.info(f"[EXPORT STUDY PGN] Generated filename: {filename}")
        logger.info(f"[EXPORT STUDY PGN] Returning success response")
        logger.info("=" * 60)

        return {"success": True, "pgn": combined_pgn, "filename": filename}
    except HTTPException as he:
        logger.error(f"[EXPORT STUDY PGN] HTTPException: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"[EXPORT STUDY PGN] Unexpected error: {type(e).__name__}")
        logger.error(f"[EXPORT STUDY PGN] Error message: {str(e)}")
        logger.error(f"[EXPORT STUDY PGN] Error details:", exc_info=True)
        return {"success": False, "error": str(e)}

def _sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    Removes or replaces characters that are invalid in filenames.
    """
    # Replace invalid characters with dash
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '-')

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')

    # Replace multiple spaces or dashes with single dash
    while '  ' in sanitized:
        sanitized = sanitized.replace('  ', ' ')
    while '--' in sanitized:
        sanitized = sanitized.replace('--', '-')

    # Limit length to avoid filesystem issues (max 255 bytes, leave room for .pgn)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]

    return sanitized or 'untitled'


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
        "Site": "catachess.com",
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

    if movetext == "*":
        return f"{header_str}\n\n*"
    return f"{header_str}\n\n{movetext} {headers['Result']}"
