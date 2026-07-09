"""
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

Patch study tree API helpers for reading, saving, and exporting chapter tree
JSON. Save requests use canonical and verified client content hashes to reduce
duplicate R2 writes without changing the persisted tree schema.
"""

import hashlib
import json
import logging
from typing import Optional
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .models import StudyTreeDTO, TreeResponse
from modules.workspace.api.deps import get_current_user_id, get_event_bus, get_node_service
from modules.workspace.storage.r2_client import R2Client, create_r2_client_from_env
from modules.workspace.storage.keys import R2Keys
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.session import get_session
from modules.workspace.domain.policies.permissions import require_node_write_access
from modules.workspace.domain.services.node_service import NodeNotFoundError, NodeService, PermissionDeniedError
from modules.workspace.events.bus import EventBus, publish_chapter_tree_saved

router = APIRouter(prefix="/study-patch", tags=["study-patch"])
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("[STUDY PATCH API] Router initialized with prefix: /study-patch")
logger.info("[STUDY PATCH API] This module provides PGN export endpoints")
logger.info("=" * 80)

def _normalize_sha256(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip().lower()
    if len(normalized) != 64:
        return None
    if any(ch not in "0123456789abcdef" for ch in normalized):
        return None
    return normalized

def _is_not_found_error(error: ClientError) -> bool:
    code = error.response.get("Error", {}).get("Code", "")
    return code in {"404", "NoSuchKey", "NotFound"}

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

async def _get_chapter_and_study_node(
    chapter_id: str,
    user_id: str,
    study_repo: StudyRepository,
    node_service: NodeService,
):
    """Resolve a chapter to its parent study node and enforce read access."""
    chapter = await study_repo.get_chapter_by_id(chapter_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    try:
        study_node = await node_service.get_node(chapter.study_id, actor_id=user_id)
    except NodeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionDeniedError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter, study_node

async def _require_chapter_tree_write(
    chapter_id: str,
    user_id: str,
    study_repo: StudyRepository,
    node_service: NodeService,
):
    """Resolve a chapter and require study editor/admin/owner access."""
    chapter, study_node = await _get_chapter_and_study_node(
        chapter_id,
        user_id,
        study_repo,
        node_service,
    )
    try:
        await require_node_write_access(node_service.acl_repo, study_node, user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return chapter, study_node

@router.get("/chapter/{chapter_id}/tree", response_model=TreeResponse)
async def get_chapter_tree(
    chapter_id: str,
    user_id: str = Depends(get_current_user_id),
    r2_client: R2Client = Depends(get_r2_client),
    study_repo: StudyRepository = Depends(get_study_repo),
    node_service: NodeService = Depends(get_node_service),
):
    """Get the tree.json for a chapter from R2."""
    key = R2Keys.chapter_tree_json(chapter_id)
    try:
        chapter, _study_node = await _get_chapter_and_study_node(
            chapter_id,
            user_id,
            study_repo,
            node_service,
        )

        if not r2_client.exists(key):
            return TreeResponse(success=False, error="Tree not found")

        content = r2_client.download_json(key)
        tree_data = json.loads(content)
        return TreeResponse(
            success=True,
            tree=StudyTreeDTO(**tree_data),
            starting_fen=chapter.starting_fen,  # Include starting_fen from database
            tree_revision=chapter.tree_revision,
            tree_updated_at=chapter.tree_updated_at.isoformat() if chapter.tree_updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tree for chapter {chapter_id}: {e}")
        return TreeResponse(success=False, error=str(e))

@router.get("/chapter/{chapter_id}/tree-meta")
async def get_chapter_tree_meta(
    chapter_id: str,
    user_id: str = Depends(get_current_user_id),
    study_repo: StudyRepository = Depends(get_study_repo),
    node_service: NodeService = Depends(get_node_service),
):
    """Return lightweight chapter tree revision metadata for refresh polling."""
    try:
        chapter, _study_node = await _get_chapter_and_study_node(
            chapter_id,
            user_id,
            study_repo,
            node_service,
        )
        return {
            "success": True,
            "tree_revision": chapter.tree_revision,
            "tree_updated_at": chapter.tree_updated_at.isoformat() if chapter.tree_updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tree metadata for chapter {chapter_id}: {e}")
        return {"success": False, "error": str(e)}

@router.put("/chapter/{chapter_id}/tree", response_model=TreeResponse)
async def put_chapter_tree(
    chapter_id: str,
    tree: StudyTreeDTO,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    r2_client: R2Client = Depends(get_r2_client),
    study_repo: StudyRepository = Depends(get_study_repo),
    node_service: NodeService = Depends(get_node_service),
    event_bus: EventBus = Depends(get_event_bus),
):
    """Save the tree.json for a chapter to R2."""
    chapter, study_node = await _require_chapter_tree_write(
        chapter_id,
        user_id,
        study_repo,
        node_service,
    )
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
        client_hash = _normalize_sha256(request.headers.get("X-Tree-Hash"))
        raw_body_hash: Optional[str] = None
        if client_hash:
            try:
                raw_body_hash = hashlib.sha256(await request.body()).hexdigest()
            except Exception as hash_error:
                logger.warning(f"Failed to hash raw tree request body for chapter {chapter_id}: {hash_error}")

        content = tree.model_dump_json()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        verified_client_hash = client_hash if client_hash and client_hash == raw_body_hash else None

        if client_hash and not verified_client_hash:
            logger.warning(
                "Ignoring mismatched tree hash for chapter %s (header=%s raw_body=%s)",
                chapter_id,
                client_hash,
                raw_body_hash,
            )

        try:
            metadata = r2_client.get_metadata(key)
            stored_content_hash = metadata.get("content-hash")
            stored_client_hash = metadata.get("client-tree-hash")
            # `content-hash` is generated from the canonical Pydantic JSON that
            # is uploaded to R2. `client-tree-hash` is the verified raw request
            # body hash from X-Tree-Hash and handles exact repeat client saves.
            if stored_content_hash == content_hash or (
                verified_client_hash and stored_client_hash == verified_client_hash
            ):
                logger.info(
                    "Tree save skipped for chapter %s; content hash unchanged (%s)",
                    chapter_id,
                    content_hash,
                )
                return TreeResponse(
                    success=True,
                    tree_revision=chapter.tree_revision,
                    tree_updated_at=chapter.tree_updated_at.isoformat() if chapter.tree_updated_at else None,
                )
        except ClientError as metadata_error:
            if not _is_not_found_error(metadata_error):
                logger.warning(
                    "Could not inspect existing tree metadata for chapter %s: %s",
                    chapter_id,
                    metadata_error,
                )

        upload_metadata = {"client-tree-hash": verified_client_hash} if verified_client_hash else None
        upload_result = r2_client.upload_json(key, content, metadata=upload_metadata)
        chapter.pgn_hash = upload_result.content_hash
        chapter.pgn_size = upload_result.size
        chapter.r2_etag = upload_result.etag
        chapter.pgn_status = "ready"
        chapter = await study_repo.mark_chapter_tree_saved(chapter)
        workspace_id = study_node.path.strip("/").split("/")[0] if study_node.path else None
        await publish_chapter_tree_saved(
            event_bus,
            actor_id=user_id,
            study_id=chapter.study_id,
            chapter_id=chapter_id,
            revision=chapter.tree_revision,
            content_hash=upload_result.content_hash,
            workspace_id=workspace_id,
        )
        logger.info(
            "Tree saved for chapter %s (size: %s bytes, content_hash: %s)",
            chapter_id,
            upload_result.size,
            upload_result.content_hash,
        )
        if verified_client_hash:
            logger.info(f"Verified client tree hash for chapter {chapter_id}: {verified_client_hash}")
        return TreeResponse(
            success=True,
            tree_revision=chapter.tree_revision,
            tree_updated_at=chapter.tree_updated_at.isoformat() if chapter.tree_updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save tree for chapter {chapter_id}: {e}")
        return TreeResponse(success=False, error=str(e))

@router.get("/chapter/{chapter_id}/pgn-export")
async def export_chapter_pgn(
    chapter_id: str,
    user_id: str = Depends(get_current_user_id),
    r2_client: R2Client = Depends(get_r2_client),
    study_repo: StudyRepository = Depends(get_study_repo),
    node_service: NodeService = Depends(get_node_service),
):
    """Export the tree.json as a PGN string."""
    logger.info("=" * 60)
    logger.info(f"[EXPORT CHAPTER PGN] ENDPOINT CALLED")
    logger.info(f"[EXPORT CHAPTER PGN] Chapter ID: {chapter_id}")
    logger.info("=" * 60)

    key = R2Keys.chapter_tree_json(chapter_id)
    logger.info(f"[EXPORT CHAPTER PGN] R2 Key: {key}")

    try:
        chapter, _study_node = await _get_chapter_and_study_node(
            chapter_id,
            user_id,
            study_repo,
            node_service,
        )
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
    user_id: str = Depends(get_current_user_id),
    r2_client: R2Client = Depends(get_r2_client),
    study_repo: StudyRepository = Depends(get_study_repo),
    node_service: NodeService = Depends(get_node_service),
):
    """Export all chapters in a study as concatenated PGN.

    Chapters that have not yet been saved (no tree in R2) are skipped
    gracefully; the response includes a `skipped_chapters` list so the
    client can surface a warning when needed.
    """
    logger.info(f"[EXPORT STUDY PGN] study_id={study_id}")

    try:
        await node_service.get_node(study_id, actor_id=user_id)
        study = await study_repo.get_study_by_id(study_id)
        if not study:
            raise HTTPException(status_code=404, detail=f"Study not found: {study_id}")

        study_title = getattr(study, 'title', None) or 'Study'
        chapters = await study_repo.get_chapters_for_study(study_id, order_by_order=True)
        logger.info(f"[EXPORT STUDY PGN] study='{study_title}', chapters={len(chapters) if chapters else 0}")

        if not chapters:
            safe_title = _sanitize_filename(study_title)
            return {"success": True, "pgn": "", "filename": f"{safe_title}.pgn", "skipped_chapters": []}

        pgn_blocks: list[str] = []
        skipped_chapters: list[dict] = []

        for idx, chapter in enumerate(chapters):
            chapter_title = getattr(chapter, 'title', None) or f'Chapter {idx + 1}'
            key = R2Keys.chapter_tree_json(chapter.id)

            if not r2_client.exists(key):
                # Chapter exists in DB but has never been saved to the tree store.
                # Skip it rather than aborting the entire export.
                logger.warning(
                    f"[EXPORT STUDY PGN] Skipping chapter '{chapter_title}' ({chapter.id}) — no tree in R2"
                )
                skipped_chapters.append({"id": chapter.id, "title": chapter_title})
                continue

            try:
                content = r2_client.download_json(key)
                tree_data = json.loads(content)
                tree = StudyTreeDTO(**tree_data)
                pgn = _tree_to_pgn(tree, chapter)
                pgn_blocks.append(pgn)
                logger.info(f"[EXPORT STUDY PGN] chapter {idx + 1}/{len(chapters)} '{chapter_title}': {len(pgn)} chars")
            except Exception as chapter_err:
                # Corrupt / unreadable tree — skip with warning instead of aborting.
                logger.error(
                    f"[EXPORT STUDY PGN] Failed to export chapter '{chapter_title}' ({chapter.id}): {chapter_err}",
                    exc_info=True
                )
                skipped_chapters.append({"id": chapter.id, "title": chapter_title, "error": str(chapter_err)})

        combined_pgn = "\n\n".join(pgn_blocks)
        safe_title = _sanitize_filename(study_title)
        filename = f"{safe_title}.pgn"

        logger.info(
            f"[EXPORT STUDY PGN] Done — {len(pgn_blocks)} exported, "
            f"{len(skipped_chapters)} skipped, total {len(combined_pgn)} chars"
        )
        return {
            "success": True,
            "pgn": combined_pgn,
            "filename": filename,
            "skipped_chapters": skipped_chapters,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXPORT STUDY PGN] Unexpected error: {type(e).__name__}: {e}", exc_info=True)
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
