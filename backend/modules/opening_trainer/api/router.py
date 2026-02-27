"""Opening Trainer progress APIs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.security.current_user import get_current_user
from core.log.log_api import logger
from models.user import User
from modules.opening_trainer.db import get_opening_trainer_db
from modules.opening_trainer.service import (
    build_eligibility_summary,
    build_unit_catalog,
    normalize_fen_key,
)
from modules.opening_trainer.schemas import (
    OpeningTrainerColor,
    OpeningTrainerEligibilityResponse,
    OpeningTrainerMode,
    OpeningTrainerUnitsResponse,
    OpeningTrainerProgressItem,
    OpeningTrainerProgressListResponse,
    OpeningTrainerProgressUpsertRequest,
)
from modules.workspace.api.deps import (
    get_current_user_id as get_workspace_user_id,
    get_study_repository as get_workspace_study_repository,
    get_variation_repository as get_workspace_variation_repository,
)
from modules.workspace.api.deps_core import get_node_service
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.repos.variation_repo import VariationRepository
from modules.workspace.domain.models.types import NodeType
from modules.workspace.domain.services.node_service import (
    NodeNotFoundError,
    NodeService,
    PermissionDeniedError,
)

router = APIRouter(prefix="/api/v1/opening-trainer", tags=["opening-trainer"])
MAX_PROGRESS_FENS = 500


async def _load_study_context(
    *,
    study_id: str,
    user_id: str,
    node_service: NodeService,
    study_repo: StudyRepository,
    variation_repo: VariationRepository,
) -> tuple[list, dict[str, list]]:
    try:
        node = await node_service.get_node(study_id, actor_id=user_id)
    except NodeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    if node.node_type != NodeType.STUDY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node {study_id} is not a study",
        )

    chapters = list(await study_repo.get_chapters_for_study(study_id, order_by_order=True))
    variations_by_chapter: dict[str, list] = {}
    for chapter in chapters:
        variations_by_chapter[chapter.id] = list(
            await variation_repo.get_variations_for_chapter(chapter.id)
        )

    return chapters, variations_by_chapter


@router.get(
    "/studies/{study_id}/eligibility",
    response_model=OpeningTrainerEligibilityResponse,
)
async def get_study_eligibility(
    study_id: str,
    user_id: str = Depends(get_workspace_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_workspace_study_repository),
    variation_repo: VariationRepository = Depends(get_workspace_variation_repository),
):
    chapters, variations_by_chapter = await _load_study_context(
        study_id=study_id,
        user_id=user_id,
        node_service=node_service,
        study_repo=study_repo,
        variation_repo=variation_repo,
    )
    summary = build_eligibility_summary(chapters, variations_by_chapter)
    return OpeningTrainerEligibilityResponse(
        eligible=summary["eligible"],
        reasons=summary["reasons"],
        stats=summary["stats"],
    )


@router.get(
    "/studies/{study_id}/units",
    response_model=OpeningTrainerUnitsResponse,
)
async def get_study_units(
    study_id: str,
    mode: OpeningTrainerMode = Query(default=OpeningTrainerMode.chapter),
    color: OpeningTrainerColor = Query(default=OpeningTrainerColor.white),
    user_id: str = Depends(get_workspace_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_workspace_study_repository),
    variation_repo: VariationRepository = Depends(get_workspace_variation_repository),
):
    chapters, variations_by_chapter = await _load_study_context(
        study_id=study_id,
        user_id=user_id,
        node_service=node_service,
        study_repo=study_repo,
        variation_repo=variation_repo,
    )
    catalog = build_unit_catalog(
        study_id=study_id,
        mode=mode.value,
        trainee_color=color.value,
        chapters=chapters,
        variations_by_chapter=variations_by_chapter,
    )
    if not catalog["eligibility"]["eligible"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Study is not eligible for opening trainer",
                "reasons": catalog["eligibility"]["reasons"],
            },
        )
    return catalog


@router.get("/progress", response_model=OpeningTrainerProgressListResponse)
def get_progress(
    fens_brackets: list[str] = Query(default_factory=list, alias="fens[]"),
    fens_plain: list[str] = Query(default_factory=list, alias="fens"),
    color: OpeningTrainerColor = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_opening_trainer_db),
):
    merged_fens = [*(fens_brackets or []), *(fens_plain or [])]
    normalized_fens: list[str] = []
    seen: set[str] = set()
    for fen in merged_fens:
        normalized = normalize_fen_key(fen)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_fens.append(normalized)

    if not normalized_fens:
        return OpeningTrainerProgressListResponse(items=[])
    if len(normalized_fens) > MAX_PROGRESS_FENS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"fens size exceeds max limit ({MAX_PROGRESS_FENS})",
        )

    stmt = text("""
        SELECT
            from_fen,
            move_san,
            color,
            correct_count,
            wrong_count,
            consecutive_correct,
            mastered,
            last_practiced_at
        FROM opening_trainer_moves
        WHERE user_id = :user_id
          AND color = :color
          AND from_fen IN :fens
    """).bindparams(bindparam("fens", expanding=True))

    try:
        result = db.execute(
            stmt,
            {
                "user_id": current_user.id,
                "color": color.value,
                "fens": normalized_fens,
            },
        )
    except SQLAlchemyError as exc:
        logger.error(f"opening trainer get progress failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query opening trainer progress",
        ) from exc

    items = [
        OpeningTrainerProgressItem(
            from_fen=row.from_fen,
            move_san=row.move_san,
            color=row.color,
            correct_count=row.correct_count,
            wrong_count=row.wrong_count,
            consecutive_correct=row.consecutive_correct,
            mastered=row.mastered,
            last_practiced_at=row.last_practiced_at,
        )
        for row in result
    ]
    return OpeningTrainerProgressListResponse(items=items)


@router.post("/progress", response_model=OpeningTrainerProgressItem)
def upsert_progress(
    body: OpeningTrainerProgressUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_opening_trainer_db),
):
    from_fen = normalize_fen_key(body.from_fen)
    move_san = body.move_san.strip()
    if not from_fen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid from_fen",
        )
    if not move_san:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid move_san",
        )

    stmt = text("""
        INSERT INTO opening_trainer_moves (
            user_id,
            from_fen,
            move_san,
            color,
            correct_count,
            wrong_count,
            consecutive_correct,
            mastered,
            last_practiced_at,
            updated_at
        )
        VALUES (
            :user_id,
            :from_fen,
            :move_san,
            :color,
            CASE WHEN :correct THEN 1 ELSE 0 END,
            CASE WHEN :correct THEN 0 ELSE 1 END,
            CASE WHEN :correct THEN 1 ELSE 0 END,
            false,
            NOW(),
            NOW()
        )
        ON CONFLICT (user_id, from_fen, move_san, color)
        DO UPDATE SET
            correct_count = opening_trainer_moves.correct_count + CASE WHEN :correct THEN 1 ELSE 0 END,
            wrong_count = opening_trainer_moves.wrong_count + CASE WHEN :correct THEN 0 ELSE 1 END,
            consecutive_correct = CASE
                WHEN :correct THEN opening_trainer_moves.consecutive_correct + 1
                ELSE 0
            END,
            mastered = CASE
                WHEN :correct THEN (opening_trainer_moves.consecutive_correct + 1) >= 3
                ELSE false
            END,
            last_practiced_at = NOW(),
            updated_at = NOW()
        RETURNING
            from_fen,
            move_san,
            color,
            correct_count,
            wrong_count,
            consecutive_correct,
            mastered,
            last_practiced_at
    """)

    params = {
        "user_id": current_user.id,
        "from_fen": from_fen,
        "move_san": move_san,
        "color": body.color.value,
        "correct": body.correct,
    }

    try:
        row = db.execute(stmt, params).one()
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(f"opening trainer upsert failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save opening trainer progress",
        ) from exc

    return OpeningTrainerProgressItem(
        from_fen=row.from_fen,
        move_san=row.move_san,
        color=row.color,
        correct_count=row.correct_count,
        wrong_count=row.wrong_count,
        consecutive_correct=row.consecutive_correct,
        mastered=row.mastered,
        last_practiced_at=row.last_practiced_at,
    )
