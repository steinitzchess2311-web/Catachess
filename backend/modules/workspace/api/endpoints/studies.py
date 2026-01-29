"""
Study endpoints.
"""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace.api.deps import (
    get_current_user_id,
    get_event_bus,
    get_event_repo,
    get_node_repo,
    get_node_service,
)
from modules.workspace.api.schemas.annotation import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    SetNAGRequest,
)
from modules.workspace.api.schemas.pgn_clip import (
    PgnClipPreviewResponse,
    PgnClipRequest,
    PgnClipResponse,
    PgnExportRequest,
)
from modules.workspace.api.schemas.study import (
    ChapterCreate,
    ChapterUpdate,
    ChapterImportPGN,
    ChapterResponse,
    ImportResultResponse,
    StudyCreate,
    StudyImportPGN,
    StudyResponse,
    StudyUpdate,
    StudyWithChaptersResponse,
    ChapterPgnResponse,
)
from modules.workspace.api.schemas.variation import (
    DemoteVariationRequest,
    MainlineMovesResponse,
    MoveCreate,
    MoveResponse,
    PromoteVariationRequest,
    ReorderVariationsRequest,
)
from modules.workspace.domain.models.move_annotation import (
    AddMoveAnnotationCommand,
    SetNAGCommand,
    UpdateMoveAnnotationCommand,
)
from modules.workspace.domain.models.node import CreateNodeCommand
from modules.workspace.domain.models.study import CreateStudyCommand, ImportPGNCommand, UpdateStudyCommand
from modules.workspace.domain.models.types import NodeType, Visibility
from modules.workspace.domain.models.variation import (
    AddMoveCommand,
    DeleteMoveCommand,
    PromoteVariationCommand,
)
from modules.workspace.db.repos.event_repo import EventRepository
from modules.workspace.db.repos.node_repo import NodeRepository
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.tables.studies import Chapter as ChapterTable
from modules.workspace.db.repos.variation_repo import VariationRepository
from modules.workspace.db.session import get_session
from modules.workspace.domain.services.chapter_import_service import ChapterImportError, ChapterImportService, StudyFullError
from modules.workspace.domain.services.node_service import NodeNotFoundError, NodeService, NodeServiceError, PermissionDeniedError
from modules.workspace.domain.services.pgn_clip_service import PgnClipService
from modules.workspace.domain.services.pgn_sync_service import PgnSyncService
from modules.workspace.domain.services.study_service import (
    AnnotationAlreadyExistsError,
    AnnotationNotFoundError,
    InvalidMoveError,
    MoveNotFoundError,
    StudyService,
)
from modules.workspace.domain.services.variation_service import (
    InvalidOperationError,
    OptimisticLockError,
    VariationNotFoundError,
    VariationService,
)
from modules.workspace.events.bus import EventBus, publish_chapter_created
from modules.workspace.storage.keys import R2Keys
from modules.workspace.storage.r2_client import R2Client, create_r2_client_from_env
from backend.core.real_pgn.parser import parse_pgn
from patch.backend.study.converter import convert_nodetree_to_dto
from modules.workspace.pgn.serializer.from_variations import build_mainline_moves
from ulid import ULID
from datetime import datetime, timezone

# New v2 imports for /show and /fen endpoints
from modules.workspace.pgn_v2.adapters import db_to_tree
from modules.workspace.db.tables.variations import Variation, MoveAnnotation
from backend.core.real_pgn.show import build_show
from backend.core.real_pgn.fen import apply_move
from backend.core.config import settings # New import

from patch.backend.study.api import router as study_patch_router

router = APIRouter(prefix="/studies", tags=["studies"])
router.include_router(study_patch_router)
logger = logging.getLogger(__name__)


@router.put("/{study_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def update_study(study_id: str) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


async def get_variation_repo(
    session: AsyncSession = Depends(get_session),
) -> VariationRepository:
    return VariationRepository(session)


async def get_study_repository(
    session: AsyncSession = Depends(get_session),
) -> StudyRepository:
    return StudyRepository(session)


async def get_study_service(
    session: AsyncSession = Depends(get_session),
    variation_repo: VariationRepository = Depends(get_variation_repo),
    event_bus: EventBus = Depends(get_event_bus),
    study_repo: StudyRepository = Depends(get_study_repository),
) -> StudyService:
    r2_client = create_r2_client_from_env()
    pgn_sync = PgnSyncService(study_repo, variation_repo, r2_client)
    return StudyService(
        session,
        variation_repo,
        event_bus,
        pgn_sync_service=pgn_sync,
    )


async def get_variation_service(
    session: AsyncSession = Depends(get_session),
    variation_repo: VariationRepository = Depends(get_variation_repo),
    event_bus: EventBus = Depends(get_event_bus),
) -> VariationService:
    return VariationService(session, variation_repo, event_bus)


async def get_chapter_import_service(
    node_service: NodeService = Depends(get_node_service),
    node_repo: NodeRepository = Depends(get_node_repo),
    study_repo: StudyRepository = Depends(get_study_repository),
    variation_repo: VariationRepository = Depends(get_variation_repo),
    event_bus: EventBus = Depends(get_event_bus),
) -> ChapterImportService:
    r2_client = create_r2_client_from_env()
    return ChapterImportService(
        node_service, node_repo, study_repo, variation_repo, r2_client, event_bus
    )


async def get_pgn_clip_service(
    study_repo: StudyRepository = Depends(get_study_repository),
    variation_repo: VariationRepository = Depends(get_variation_repo),
    event_repo: EventRepository = Depends(get_event_repo),
    event_bus: EventBus = Depends(get_event_bus),
) -> PgnClipService:
    r2_client = create_r2_client_from_env()
    return PgnClipService(
        study_repo, variation_repo, event_repo, event_bus, r2_client
    )


@router.post("", response_model=StudyResponse, status_code=status.HTTP_201_CREATED)
async def create_study(
    data: StudyCreate,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_study_repository),
) -> StudyResponse:
    """
    Create a new study.

    Creates both a node and study entity.
    """
    try:
        # Create study node
        command = CreateNodeCommand(
            node_type=NodeType.STUDY,
            title=data.title,
            owner_id=user_id,
            parent_id=data.parent_id,
            visibility=data.visibility,
        )

        node = await node_service.create_node(command, actor_id=user_id)

        await study_repo.ensure_study(
            node.id,
            description=data.description,
            is_public=data.visibility == Visibility.PUBLIC,
            tags=data.tags,
        )

        return StudyResponse(
            id=node.id,
            title=node.title,
            description=data.description,
            owner_id=node.owner_id,
            visibility=node.visibility,
            chapter_count=0,
            is_public=False,
            tags=data.tags,
            parent_id=node.parent_id,
            path=node.path,
            depth=node.depth,
            version=node.version,
            created_at=node.created_at,
            updated_at=node.updated_at,
            deleted_at=node.deleted_at,
        )

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NodeServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/import-pgn", response_model=ImportResultResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_pgn(
    data: StudyImportPGN,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    import_service: ChapterImportService = Depends(get_chapter_import_service),
) -> ImportResultResponse:
    """
    Import PGN content to create study/studies with chapters.

    If PGN has <= 64 chapters: creates single study
    If PGN has > 64 chapters and auto_split=True: creates folder with multiple studies
    """
    try:
        command = ImportPGNCommand(
            parent_id=data.parent_id,
            owner_id=user_id,
            pgn_content=data.pgn_content,
            base_title=data.base_title,
            auto_split=data.auto_split,
            visibility=data.visibility,
        )

        result = await import_service.import_pgn(command, actor_id=user_id, background_tasks=background_tasks)

        return ImportResultResponse(
            total_chapters=result.total_chapters,
            studies_created=result.studies_created,
            folder_id=result.folder_id,
            was_split=result.was_split,
            single_study=result.single_study,
        )

    except ChapterImportError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{study_id}/chapters/import-pgn",
    response_model=ImportResultResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def import_pgn_into_study(
    study_id: str,
    data: ChapterImportPGN,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_study_repository),
    import_service: ChapterImportService = Depends(get_chapter_import_service),
) -> ImportResultResponse:
    """Import PGN content into an existing study as new chapters."""
    try:
        node = await node_service.get_node(study_id, actor_id=user_id)
        if node.node_type != NodeType.STUDY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node is not a study",
            )

        await study_repo.ensure_study(
            study_id,
            description=None,
            is_public=node.visibility == Visibility.PUBLIC,
            tags=None,
        )

        result = await import_service.import_pgn_into_study(
            study_id, data.pgn_content, actor_id=user_id, background_tasks=background_tasks
        )
        return ImportResultResponse(
            total_chapters=result.total_chapters,
            studies_created=result.studies_created,
            folder_id=result.folder_id,
            was_split=result.was_split,
            single_study=result.single_study,
        )

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StudyFullError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ChapterImportError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{study_id}", response_model=StudyWithChaptersResponse)
async def get_study(
    study_id: str,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_study_repository),
) -> StudyWithChaptersResponse:
    """Get study with all chapters."""
    try:
        # Get node to check permissions
        node = await node_service.get_node(study_id, actor_id=user_id)

        if node.node_type != NodeType.STUDY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node is not a study"
            )

        # Get study entity
        study = await study_repo.ensure_study(
            study_id,
            description=None,
            is_public=node.visibility == Visibility.PUBLIC,
            tags=None,
        )

        # Get chapters for study
        chapters = await study_repo.get_chapters_for_study(study_id, order_by_order=True)

        # Build response
        study_response = StudyResponse(
            id=study.id,
            title=node.title,
            description=study.description,
            owner_id=node.owner_id,
            visibility=node.visibility,
            chapter_count=study.chapter_count,
            is_public=study.is_public,
            tags=study.tags,
            parent_id=node.parent_id,
            path=node.path,
            depth=node.depth,
            version=node.version,
            created_at=node.created_at,
            updated_at=node.updated_at,
            deleted_at=node.deleted_at,
        )

        chapter_responses = [_build_chapter_response(chapter) for chapter in chapters]

        return StudyWithChaptersResponse(
            study=study_response,
            chapters=chapter_responses,
        )

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/{study_id}/chapters",
    response_model=list[ChapterResponse],
    status_code=status.HTTP_200_OK,
)
async def get_study_chapters(
    study_id: str,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_study_repository),
) -> list[ChapterResponse]:
    """Get chapter list for a study."""
    try:
        node = await node_service.get_node(study_id, actor_id=user_id)
        if node.node_type != NodeType.STUDY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node is not a study",
            )

        chapters = await study_repo.get_chapters_for_study(study_id, order_by_order=True)
        return [_build_chapter_response(chapter) for chapter in chapters]
    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{study_id}/chapters",
    response_model=ChapterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chapter(
    study_id: str,
    data: ChapterCreate,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_study_repository),
) -> ChapterResponse:
    """Create a new chapter with an empty PGN."""
    try:
        node = await node_service.get_node(study_id, actor_id=user_id)
        if node.node_type != NodeType.STUDY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node is not a study",
            )

        study = await study_repo.get_study_by_id(study_id)
        if not study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Study {study_id} not found",
            )

        existing = await study_repo.get_chapters_for_study(
            study_id, order_by_order=True
        )
        max_order = max(
            (chapter.order for chapter in existing if chapter.order is not None),
            default=-1,
        )
        order = max_order + 1

        chapter_id = str(ULID())
        r2_key = R2Keys.chapter_tree_json(chapter_id)
        tree_content = {
            "version": "v1",
            "rootId": "root",
            "nodes": {
                "root": {
                    "id": "root",
                    "parentId": None,
                    "san": "",
                    "children": [],
                    "comment": None,
                    "nags": [],
                },
            },
            "meta": {
                "result": "*",
            },
        }

        r2_client = create_r2_client_from_env()
        upload_result = r2_client.upload_json(
            key=r2_key,
            content=json.dumps(tree_content),
            metadata={
                "study_id": study_id,
                "chapter_id": chapter_id,
                "order": str(order),
            },
        )

        chapter = ChapterTable(
            id=chapter_id,
            study_id=study_id,
            title=data.title,
            order=order,
            white=None,
            black=None,
            event=data.title,
            date=None,
            result="*",
            r2_key=r2_key,
            pgn_hash=upload_result.content_hash,
            pgn_size=upload_result.size,
            pgn_status="ready",
            r2_etag=upload_result.etag,
            last_synced_at=datetime.now(timezone.utc),
        )

        await study_repo.create_chapter(chapter)
        await study_repo.update_chapter_count(study_id)

        workspace_id = node.path.strip("/").split("/")[0] if node.path else None
        await publish_chapter_created(
            event_bus,
            actor_id=user_id,
            study_id=study_id,
            chapter_id=chapter_id,
            title=chapter.title,
            order=order,
            r2_key=r2_key,
            workspace_id=workspace_id,
        )

        return ChapterResponse.model_validate(chapter)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put(
    "/{study_id}/chapters/{chapter_id}",
    response_model=ChapterResponse,
    status_code=status.HTTP_200_OK,
)
async def update_chapter(
    study_id: str,
    chapter_id: str,
    data: ChapterUpdate,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_study_repository),
    event_bus: EventBus = Depends(get_event_bus),
) -> ChapterResponse:
    """Update chapter metadata (title)."""
    try:
        node = await node_service.get_node(study_id, actor_id=user_id)
        if node.node_type != NodeType.STUDY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node is not a study",
            )

        chapter = await study_repo.get_chapter_by_id(chapter_id)
        if not chapter or chapter.study_id != study_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_id} not found in study {study_id}",
            )

        chapter.title = data.title
        chapter.event = data.title
        updated = await study_repo.update_chapter(chapter)

        return ChapterResponse.model_validate(updated)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

def _build_chapter_response(chapter: ChapterTable) -> ChapterResponse:
    response_data = chapter.__dict__
    db_status = response_data.get("pgn_status")

    # Priority: Use DB pgn_status if set, otherwise infer from metadata
    if db_status in ("ready", "error", "mismatch", "missing"):
        final_status = db_status
    elif not response_data.get("r2_key"):
        # r2_key is NOT NULL, so this shouldn't happen
        final_status = "missing"
    elif not response_data.get("pgn_hash"):
        # Empty chapter (no moves) can have r2_key but no pgn_hash
        # This is valid - treat as ready if no explicit status
        final_status = "ready"
    else:
        final_status = "ready"

    response_data["pgn_status"] = final_status
    return ChapterResponse.model_validate(response_data)


@router.post(
    "/{study_id}/pgn/clip",
    response_model=PgnClipResponse,
    status_code=status.HTTP_200_OK,
)
async def clip_pgn(
    study_id: str,
    data: PgnClipRequest,
    user_id: str = Depends(get_current_user_id),
    clip_service: PgnClipService = Depends(get_pgn_clip_service),
) -> PgnClipResponse:
    """
    Clip or export PGN for a chapter.

    Supports clip, no-comment, raw, and clean mainline exports.
    """
    try:
        if data.mode == "clip":
            if not data.move_path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="move_path is required for clip mode",
                )
            result = await clip_service.clip_from_move(
                chapter_id=data.chapter_id,
                move_path=data.move_path,
                actor_id=user_id,
                for_clipboard=data.for_clipboard,
            )
            return PgnClipResponse(
                pgn_text=result.pgn_text,
                export_mode="clip",
                move_path=result.move_path,
                moves_removed=result.moves_removed,
                variations_removed=result.variations_removed,
                timestamp=result.timestamp,
            )

        if data.mode == "no_comment":
            result = await clip_service.export_no_comments(
                chapter_id=data.chapter_id,
                actor_id=user_id,
                for_clipboard=data.for_clipboard,
            )
            return PgnClipResponse(
                pgn_text=result.pgn_text,
                export_mode=result.export_mode,
                timestamp=result.timestamp,
            )

        if data.mode == "raw":
            result = await clip_service.export_raw(
                chapter_id=data.chapter_id,
                actor_id=user_id,
                for_clipboard=data.for_clipboard,
            )
            return PgnClipResponse(
                pgn_text=result.pgn_text,
                export_mode=result.export_mode,
                timestamp=result.timestamp,
            )

        if data.mode == "clean":
            result = await clip_service.export_clean(
                chapter_id=data.chapter_id,
                actor_id=user_id,
            )
            return PgnClipResponse(
                pgn_text=result.pgn_text,
                export_mode=result.export_mode,
                timestamp=result.timestamp,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported mode '{data.mode}'",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{study_id}/pgn/clip/preview",
    response_model=PgnClipPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def preview_clip_pgn(
    study_id: str,
    chapter_id: str,
    move_path: str,
    user_id: str = Depends(get_current_user_id),
    clip_service: PgnClipService = Depends(get_pgn_clip_service),
) -> PgnClipPreviewResponse:
    """
    Preview PGN clip results.

    Example:
        GET /studies/{study_id}/pgn/clip/preview?chapter_id=ch1&move_path=main.12
    """
    try:
        preview = await clip_service.get_clip_preview(chapter_id, move_path)
        return PgnClipPreviewResponse(**preview)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{study_id}/pgn/export/no-comment",
    response_model=PgnClipResponse,
    status_code=status.HTTP_200_OK,
)
async def export_no_comment_pgn_endpoint(
    study_id: str,
    data: PgnExportRequest,
    user_id: str = Depends(get_current_user_id),
    clip_service: PgnClipService = Depends(get_pgn_clip_service),
) -> PgnClipResponse:
    """
    Export PGN with variations, without comments.

    Example:
        POST /studies/{study_id}/pgn/export/no-comment
    """
    try:
        result = await clip_service.export_no_comments(
            chapter_id=data.chapter_id,
            actor_id=user_id,
            for_clipboard=data.for_clipboard,
        )
        return PgnClipResponse(
            pgn_text=result.pgn_text,
            export_mode=result.export_mode,
            timestamp=result.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{study_id}/pgn/export/raw",
    response_model=PgnClipResponse,
    status_code=status.HTTP_200_OK,
)
async def export_raw_pgn_endpoint(
    study_id: str,
    data: PgnExportRequest,
    user_id: str = Depends(get_current_user_id),
    clip_service: PgnClipService = Depends(get_pgn_clip_service),
) -> PgnClipResponse:
    """
    Export raw PGN (mainline only).

    Example:
        POST /studies/{study_id}/pgn/export/raw
    """
    try:
        result = await clip_service.export_raw(
            chapter_id=data.chapter_id,
            actor_id=user_id,
            for_clipboard=data.for_clipboard,
        )
        return PgnClipResponse(
            pgn_text=result.pgn_text,
            export_mode=result.export_mode,
            timestamp=result.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{study_id}/pgn/export/clean",
    response_model=PgnClipResponse,
    status_code=status.HTTP_200_OK,
)
async def export_clean_pgn_endpoint(
    study_id: str,
    data: PgnExportRequest,
    user_id: str = Depends(get_current_user_id),
    clip_service: PgnClipService = Depends(get_pgn_clip_service),
) -> PgnClipResponse:
    """
    Export clean mainline (no variations, no comments).

    Example:
        POST /studies/{study_id}/pgn/export/clean
    """
    try:
        result = await clip_service.export_clean(
            chapter_id=data.chapter_id,
            actor_id=user_id,
        )
        return PgnClipResponse(
            pgn_text=result.pgn_text,
            export_mode=result.export_mode,
            timestamp=result.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def get_r2_client() -> R2Client:
    return create_r2_client_from_env()


@router.get(
    "/{study_id}/chapters/{chapter_id}/pgn",
    response_model=ChapterPgnResponse,
    status_code=status.HTTP_200_OK,
)
async def get_chapter_pgn(
    study_id: str,
    chapter_id: str,
    user_id: str = Depends(get_current_user_id),
    study_repo: StudyRepository = Depends(get_study_repository),
    node_service: NodeService = Depends(get_node_service),
    r2_client: R2Client = Depends(get_r2_client),
) -> ChapterPgnResponse:
    """Get PGN text and metadata for a chapter."""
    try:
        # Check permissions by getting the parent study node
        await node_service.get_node(study_id, actor_id=user_id)

        chapter = await study_repo.get_chapter_by_id(chapter_id)
        if not chapter or chapter.study_id != study_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_id} not found in study {study_id}",
            )

        tree_key = R2Keys.chapter_tree_json(chapter_id)
        r2_key = chapter.r2_key or tree_key

        if not r2_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PGN key could not be determined for chapter {chapter_id}",
            )

        pgn_text = ""
        try:
            # Stage 10+: Tree JSON is the canonical storage.
            if r2_key.endswith(".pgn"):
                # Lazy migrate legacy PGN -> tree.json
                pgn_text = r2_client.download_pgn(r2_key)
                node_tree = parse_pgn(pgn_text)
                tree_dto = convert_nodetree_to_dto(node_tree)
                upload = r2_client.upload_json(
                    key=tree_key,
                    content=tree_dto.model_dump_json(),
                    metadata={"chapter_id": chapter_id},
                )
                chapter.r2_key = tree_key
                chapter.pgn_hash = upload.content_hash
                chapter.pgn_size = upload.size
                chapter.r2_etag = upload.etag
                chapter.last_synced_at = datetime.now(timezone.utc)
                await study_repo.update_chapter(chapter)
                r2_key = tree_key

            if not r2_key.endswith(".json"):
                raise ValueError(f"Unsupported r2_key format: {r2_key}")

            if not r2_client.exists(r2_key):
                raise ValueError(f"Tree not found in R2 for chapter {chapter_id}")

            from patch.backend.study.models import StudyTreeDTO
            from patch.backend.study.api import _tree_to_pgn

            json_content = r2_client.download_json(r2_key)
            tree_data = json.loads(json_content)
            tree_dto = StudyTreeDTO(**tree_data)
            pgn_text = _tree_to_pgn(tree_dto, chapter)
                
        except Exception as e:  # Assuming a client error if download fails
            logger.error(f"Failed to retrieve PGN for chapter {chapter_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content not found or invalid in R2 for chapter {chapter_id} with key {r2_key}",
            )

        return ChapterPgnResponse(
            pgn_text=pgn_text,
            pgn_hash=chapter.pgn_hash,
            pgn_size=chapter.pgn_size,
            last_synced_at=chapter.last_synced_at,
        )
    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete(
    "/{study_id}/chapters/{chapter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chapter(
    study_id: str,
    chapter_id: str,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_study_repository),
) -> Response:
    """Delete a chapter and its stored tree."""
    try:
        node = await node_service.get_node(study_id, actor_id=user_id)
        if node.node_type != NodeType.STUDY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node is not a study",
            )

        chapter = await study_repo.get_chapter_by_id(chapter_id)
        if not chapter or chapter.study_id != study_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_id} not found in study {study_id}",
            )

        r2_client = create_r2_client_from_env()
        r2_key = chapter.r2_key or R2Keys.chapter_tree_json(chapter_id)
        try:
            r2_client.delete(r2_key)
        except Exception:
            pass

        await study_repo.delete_chapter(chapter)
        await study_repo.update_chapter_count(study_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# ============================================================================
# Phase 3: Variation Tree Editing Endpoints
# ============================================================================


@router.get(
    "/{study_id}/chapters/{chapter_id}/moves/mainline",
    response_model=MainlineMovesResponse,
    status_code=status.HTTP_200_OK,
    deprecated=True,
)
async def get_mainline_moves(
    study_id: str,
    chapter_id: str,
    user_id: str = Depends(get_current_user_id),
    variation_repo: VariationRepository = Depends(get_variation_repo),
) -> MainlineMovesResponse:
    """
    [DEPRECATED] Return mainline moves for UI rendering.

    This provides move IDs, SAN, FEN, and annotation text/version so the
    frontend can render two moves per line and edit comments reliably.
    """
    variations = await variation_repo.get_variations_for_chapter(chapter_id)
    annotations = await variation_repo.get_annotations_for_chapter(chapter_id)
    moves = build_mainline_moves(variations, annotations)
    return MainlineMovesResponse(moves=moves)


@router.post(
    "/{study_id}/chapters/{chapter_id}/moves",
    response_model=MoveResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_move(
    response: Response,
    study_id: str,
    chapter_id: str,
    data: MoveCreate,
    user_id: str = Depends(get_current_user_id),
    study_service: StudyService = Depends(get_study_service),
) -> MoveResponse:
    """
    Add a move to the variation tree.

    FEN is computed server-side from parent position + UCI move if not provided.

    Args:
        response: FastAPI response object
        study_id: Study ID
        chapter_id: Chapter ID
        data: Move data (fen is optional)
        user_id: Current user ID
        study_service: Study service

    Returns:
        Created move with ETag header

    Raises:
        404: Parent move not found
        400: Invalid move data or illegal move
    """
    try:
        command = AddMoveCommand(
            chapter_id=chapter_id,
            parent_id=data.parent_id,
            san=data.san,
            uci=data.uci,
            move_number=data.move_number,
            color=data.color,
            created_by=user_id,
            fen=data.fen,  # Optional - computed server-side if None
            rank=data.rank,
            priority=data.priority,
            visibility=data.visibility,
        )

        move = await study_service.add_move(command)

        # Set ETag header for optimistic locking
        response.headers["ETag"] = f'"{move.version}"'

        return MoveResponse.model_validate(move)

    except MoveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidMoveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{study_id}/chapters/{chapter_id}/moves/{move_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_move(
    study_id: str,
    chapter_id: str,
    move_id: str,
    user_id: str = Depends(get_current_user_id),
    study_service: StudyService = Depends(get_study_service),
) -> None:
    """
    Delete a move and all its descendants.

    Args:
        study_id: Study ID
        chapter_id: Chapter ID
        move_id: Move ID to delete
        user_id: Current user ID
        study_service: Study service

    Raises:
        404: Move not found
    """
    try:
        command = DeleteMoveCommand(
            variation_id=move_id,
            actor_id=user_id,
        )

        await study_service.delete_move(command)

    except MoveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{study_id}/chapters/{chapter_id}/variations",
    response_model=MoveResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_variation(
    response: Response,
    study_id: str,
    chapter_id: str,
    data: MoveCreate,
    user_id: str = Depends(get_current_user_id),
    study_service: StudyService = Depends(get_study_service),
) -> MoveResponse:
    """
    Add a variation (alternative move) to the tree.

    This is an alias for add_move with rank > 0.
    FEN is computed server-side from parent position + UCI move if not provided.

    Args:
        response: FastAPI response object
        study_id: Study ID
        chapter_id: Chapter ID
        data: Variation data (rank should be > 0, fen is optional)
        user_id: Current user ID
        study_service: Study service

    Returns:
        Created variation with ETag header

    Raises:
        404: Parent move not found
        400: Invalid rank (must be > 0 for variations) or illegal move
    """
    try:
        if data.rank == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Variations must have rank > 0. Use POST /moves for main line."
            )

        command = AddMoveCommand(
            chapter_id=chapter_id,
            parent_id=data.parent_id,
            san=data.san,
            uci=data.uci,
            move_number=data.move_number,
            color=data.color,
            created_by=user_id,
            fen=data.fen,  # Optional - computed server-side if None
            rank=data.rank,
            priority=data.priority,
            visibility=data.visibility,
        )

        move = await study_service.add_move(command)

        # Set ETag header for optimistic locking
        response.headers["ETag"] = f'"{move.version}"'

        return MoveResponse.model_validate(move)

    except MoveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidMoveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{study_id}/chapters/{chapter_id}/moves/{move_id}/annotations",
    response_model=AnnotationResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_annotation(
    response: Response,
    study_id: str,
    chapter_id: str,
    move_id: str,
    data: AnnotationCreate,
    user_id: str = Depends(get_current_user_id),
    study_service: StudyService = Depends(get_study_service),
) -> AnnotationResponse:
    """
    Add annotation to a move.

    Args:
        response: FastAPI response object
        study_id: Study ID
        chapter_id: Chapter ID
        move_id: Move ID
        data: Annotation data
        user_id: Current user ID
        study_service: Study service

    Returns:
        Created annotation with ETag header

    Raises:
        404: Move not found
        409: Annotation already exists for this move
    """
    try:
        command = AddMoveAnnotationCommand(
            move_id=move_id,
            author_id=user_id,
            nag=data.nag,
            text=data.text,
        )

        annotation = await study_service.add_move_annotation(command)

        # Set ETag header for optimistic locking
        response.headers["ETag"] = f'"{annotation.version}"'

        return AnnotationResponse.model_validate(annotation)

    except MoveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AnnotationAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{study_id}/chapters/{chapter_id}/annotations/{annotation_id}",
    response_model=AnnotationResponse,
    status_code=status.HTTP_200_OK,
)
async def update_annotation(
    response: Response,
    study_id: str,
    chapter_id: str,
    annotation_id: str,
    data: AnnotationUpdate,
    user_id: str = Depends(get_current_user_id),
    study_service: StudyService = Depends(get_study_service),
) -> AnnotationResponse:
    """
    Update an existing move annotation.

    The UI sends the current version to prevent silent overwrites.
    """
    try:
        command = UpdateMoveAnnotationCommand(
            annotation_id=annotation_id,
            nag=data.nag,
            text=data.text,
            version=data.version,
            actor_id=user_id,
        )
        annotation = await study_service.edit_move_annotation(command)
        response.headers["ETag"] = f'"{annotation.version}"'
        return AnnotationResponse.model_validate(annotation)
    except AnnotationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{study_id}/chapters/{chapter_id}/variations/{variation_id}/promote",
    status_code=status.HTTP_204_NO_CONTENT
)
async def promote_variation(
    study_id: str,
    chapter_id: str,
    variation_id: str,
    data: PromoteVariationRequest,
    user_id: str = Depends(get_current_user_id),
    variation_service: VariationService = Depends(get_variation_service),
    if_match: str | None = Header(None, alias="If-Match"),
) -> None:
    """
    Promote a variation to main line.

    Swaps ranks with the current main line.

    Args:
        study_id: Study ID
        chapter_id: Chapter ID
        variation_id: Variation ID to promote
        data: Promotion request (optional expected_version)
        user_id: Current user ID
        variation_service: Variation service
        if_match: If-Match header for optimistic locking

    Raises:
        404: Variation not found
        409: Version conflict (optimistic locking)
        400: Already main line
    """
    try:
        # Use If-Match header if provided and body doesn't have expected_version
        expected_version = data.expected_version
        if if_match and expected_version is None:
            # Parse version from If-Match: "1" -> 1
            expected_version = int(if_match.strip('"'))

        command = PromoteVariationCommand(
            variation_id=variation_id,
            actor_id=user_id,
            expected_version=expected_version,
        )

        await variation_service.promote_variation(command)

    except VariationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Phase 4: PGN v2 Endpoints (ShowDTO and FEN)
# ============================================================================


@router.get(
    "/{study_id}/chapters/{chapter_id}/show",
    status_code=status.HTTP_200_OK,
)
async def get_chapter_show(
    study_id: str,
    chapter_id: str,
    user_id: str = Depends(get_current_user_id),
    variation_repo: VariationRepository = Depends(get_variation_repo),
    study_repo: StudyRepository = Depends(get_study_repository),
):
    """
    Get ShowDTO for chapter rendering.

    Returns a complete rendering structure including:
    - headers: PGN headers
    - nodes: All nodes in the tree
    - render: Token stream for rendering
    - root_fen: Starting FEN position
    - result: Game result

    This is the new v2 endpoint for frontend rendering.
    """
    # Always allow ShowDTO for rendering; frontend relies on it for variations.
    r2_key = None
    try:
        chapter = await study_repo.get_chapter_by_id(chapter_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_id} not found"
            )
        r2_key = chapter.r2_key

        variations = await variation_repo.get_variations_for_chapter(chapter_id)
        annotations = await variation_repo.get_annotations_for_chapter(chapter_id)

        # Build NodeTree using v2 adapter
        tree = db_to_tree(
            variations=variations,
            annotations=annotations,
            VariationCls=Variation,
            MoveAnnotationCls=MoveAnnotation,
            chapter=chapter,
        )

        # Build ShowDTO
        show_dto = build_show(tree)

        return show_dto

    except Exception as e:
        logger.error(
            "ShowDTO failed",
            exc_info=True,
            extra={
                "study_id": study_id,
                "chapter_id": chapter_id,
                "r2_key": r2_key,
                "error_code": "pgn_show_failed",
            },
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{study_id}/chapters/{chapter_id}/fen/{node_id}",
    status_code=status.HTTP_200_OK,
)
async def get_node_fen(
    study_id: str,
    chapter_id: str,
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    variation_repo: VariationRepository = Depends(get_variation_repo),
    study_repo: StudyRepository = Depends(get_study_repository),
):
    """
    Get FEN for a specific node.

    Returns:
        { "fen": "...", "node_id": "..." }

    This endpoint allows the frontend to retrieve FEN for any node
    without loading the entire tree.
    """
    # Always allow FEN lookup for node navigation.
    r2_key = None
    try:
        variation = await variation_repo.get_variation_by_id(node_id)
        if not variation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node {node_id} not found"
            )

        if variation.chapter_id != chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Node {node_id} does not belong to chapter {chapter_id}"
            )

        chapter = await study_repo.get_chapter_by_id(chapter_id)
        if chapter:
            r2_key = chapter.r2_key

        return {
            "fen": variation.fen,
            "node_id": node_id,
            "san": variation.san,
            "uci": variation.uci,
            "move_number": variation.move_number,
            "color": variation.color,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "FEN lookup failed",
            exc_info=True,
            extra={
                "study_id": study_id,
                "chapter_id": chapter_id,
                "r2_key": r2_key,
                "error_code": "pgn_fen_failed",
            },
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
