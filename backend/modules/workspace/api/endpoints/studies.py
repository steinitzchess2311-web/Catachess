"""
Study endpoints.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.api.deps import (
    get_current_user_id,
    get_event_bus,
    get_event_repo,
    get_node_repo,
    get_node_service,
)
from workspace.api.schemas.annotation import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    SetNAGRequest,
)
from workspace.api.schemas.pgn_clip import (
    PgnClipPreviewResponse,
    PgnClipRequest,
    PgnClipResponse,
    PgnExportRequest,
)
from workspace.api.schemas.study import (
    ChapterResponse,
    ImportResultResponse,
    StudyCreate,
    StudyImportPGN,
    StudyResponse,
    StudyUpdate,
    StudyWithChaptersResponse,
)
from workspace.api.schemas.variation import (
    DemoteVariationRequest,
    MoveCreate,
    MoveResponse,
    PromoteVariationRequest,
    ReorderVariationsRequest,
)
from workspace.domain.models.move_annotation import (
    AddMoveAnnotationCommand,
    SetNAGCommand,
    UpdateMoveAnnotationCommand,
)
from workspace.domain.models.node import CreateNodeCommand
from workspace.domain.models.study import CreateStudyCommand, ImportPGNCommand, UpdateStudyCommand
from workspace.domain.models.types import NodeType
from workspace.domain.models.variation import (
    AddMoveCommand,
    DeleteMoveCommand,
    PromoteVariationCommand,
)
from workspace.db.repos.event_repo import EventRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.repos.study_repo import StudyRepository
from workspace.db.repos.variation_repo import VariationRepository
from workspace.db.session import get_session
from workspace.domain.services.chapter_import_service import ChapterImportError, ChapterImportService
from workspace.domain.services.node_service import NodeNotFoundError, NodeService, NodeServiceError, PermissionDeniedError
from workspace.domain.services.pgn_clip_service import PgnClipService
from workspace.domain.services.study_service import (
    AnnotationAlreadyExistsError,
    AnnotationNotFoundError,
    MoveNotFoundError,
    StudyService,
)
from workspace.domain.services.variation_service import (
    InvalidOperationError,
    OptimisticLockError,
    VariationNotFoundError,
    VariationService,
)
from workspace.events.bus import EventBus
from workspace.storage.r2_client import create_r2_client_from_env

router = APIRouter(prefix="/studies", tags=["studies"])


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
) -> StudyService:
    return StudyService(session, variation_repo, event_bus)


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
    event_bus: EventBus = Depends(get_event_bus),
) -> ChapterImportService:
    r2_client = create_r2_client_from_env()
    return ChapterImportService(
        node_service, node_repo, study_repo, r2_client, event_bus
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

        # TODO: Create study entity in database
        # For now, just return node info
        # This would need study_service integration

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


@router.post("/import-pgn", response_model=ImportResultResponse, status_code=status.HTTP_201_CREATED)
async def import_pgn(
    data: StudyImportPGN,
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

        result = await import_service.import_pgn(command, actor_id=user_id)

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
        study = await study_repo.get_study_by_id(study_id)
        if not study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Study {study_id} not found"
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

        chapter_responses = [
            ChapterResponse.model_validate(chapter) for chapter in chapters
        ]

        return StudyWithChaptersResponse(
            study=study_response,
            chapters=chapter_responses,
        )

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


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


# ============================================================================
# Phase 3: Variation Tree Editing Endpoints
# ============================================================================


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

    Args:
        response: FastAPI response object
        study_id: Study ID
        chapter_id: Chapter ID
        data: Move data
        user_id: Current user ID
        study_service: Study service

    Returns:
        Created move with ETag header

    Raises:
        404: Parent move not found
        400: Invalid move data
    """
    try:
        command = AddMoveCommand(
            chapter_id=chapter_id,
            parent_id=data.parent_id,
            san=data.san,
            uci=data.uci,
            fen=data.fen,
            move_number=data.move_number,
            color=data.color,
            created_by=user_id,
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

    Args:
        response: FastAPI response object
        study_id: Study ID
        chapter_id: Chapter ID
        data: Variation data (rank should be > 0)
        user_id: Current user ID
        study_service: Study service

    Returns:
        Created variation with ETag header

    Raises:
        404: Parent move not found
        400: Invalid rank (must be > 0 for variations)
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
            fen=data.fen,
            move_number=data.move_number,
            color=data.color,
            created_by=user_id,
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
