"""Opening Trainer APIs."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.log.log_api import logger
from core.security.current_user import get_current_user
from models.user import User
from modules.opening_trainer.db import get_opening_trainer_db
from modules.opening_trainer.schemas import (
    OpeningTrainerColor,
    OpeningTrainerEligibilityResponse,
    OpeningTrainerMode,
    OpeningTrainerProgressItem,
    OpeningTrainerProgressListResponse,
    OpeningTrainerProgressUpsertRequest,
    OpeningTrainerTrainingAnswerRequest,
    OpeningTrainerTrainingAnswerResponse,
    OpeningTrainerTrainingMode,
    OpeningTrainerTrainingProgress,
    OpeningTrainerTrainingStartRequest,
    OpeningTrainerTrainingStartResponse,
    OpeningTrainerUnitDetailResponse,
    OpeningTrainerUnitsResponse,
)
from modules.opening_trainer.service import (
    advance_until_prompt,
    build_eligibility_summary,
    build_unit_catalog,
    get_leaf_unit,
    get_line_by_signature,
    normalize_fen_key,
    normalize_san_for_compare,
    pick_line_for_unit,
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


_PROGRESS_UPSERT_SQL = text(
    """
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
"""
)


def _to_progress_item(row: Any) -> OpeningTrainerProgressItem:
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


def _to_training_progress(row: Any) -> OpeningTrainerTrainingProgress:
    return OpeningTrainerTrainingProgress(
        from_fen=row.from_fen,
        move_san=row.move_san,
        color=row.color,
        correct_count=row.correct_count,
        wrong_count=row.wrong_count,
        consecutive_correct=row.consecutive_correct,
        mastered=row.mastered,
        last_practiced_at=row.last_practiced_at,
    )


def _upsert_progress(
    *,
    db: Session,
    user_id: Any,
    from_fen: str,
    move_san: str,
    color: str,
    correct: bool,
) -> Any:
    try:
        row = db.execute(
            _PROGRESS_UPSERT_SQL,
            {
                "user_id": user_id,
                "from_fen": normalize_fen_key(from_fen),
                "move_san": move_san.strip(),
                "color": color,
                "correct": correct,
            },
        ).one()
        db.commit()
        return row
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(f"opening trainer progress upsert failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save opening trainer progress",
        ) from exc


def _is_step_mastered(
    *,
    db: Session,
    user_id: Any,
    step: dict[str, Any],
    trainee_color: str,
    cache: dict[tuple[str, str, str], bool],
) -> bool:
    from_fen = normalize_fen_key(step.get("from_fen"))
    move_san = (step.get("move_san") or "").strip()
    cache_key = (from_fen, move_san, trainee_color)
    if cache_key in cache:
        return cache[cache_key]

    stmt = text(
        """
        SELECT mastered
        FROM opening_trainer_moves
        WHERE user_id = :user_id
          AND from_fen = :from_fen
          AND move_san = :move_san
          AND color = :color
        LIMIT 1
        """
    )
    try:
        row = db.execute(
            stmt,
            {
                "user_id": user_id,
                "from_fen": from_fen,
                "move_san": move_san,
                "color": trainee_color,
            },
        ).first()
    except SQLAlchemyError as exc:
        logger.error(f"opening trainer mastered lookup failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query opening trainer progress",
        ) from exc

    mastered = bool(row and row.mastered)
    cache[cache_key] = mastered
    return mastered


def _normalize_fen_list(fens_brackets: list[str], fens_plain: list[str]) -> list[str]:
    merged_fens = [*(fens_brackets or []), *(fens_plain or [])]
    normalized_fens: list[str] = []
    seen: set[str] = set()
    for fen in merged_fens:
        normalized = normalize_fen_key(fen)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_fens.append(normalized)
    return normalized_fens


def _to_prompt(step: dict[str, Any] | None) -> dict[str, Any] | None:
    if step is None:
        return None
    return {
        "from_fen": normalize_fen_key(step.get("from_fen")),
        "move_san": step.get("move_san"),
        "move_uci": step.get("move_uci"),
        "color": step.get("color"),
        "move_number": step.get("move_number"),
        "ply": step.get("ply"),
    }


def _to_auto_moves(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "from_fen": normalize_fen_key(item.get("from_fen")),
            "to_fen": normalize_fen_key(item.get("to_fen")),
            "move_san": item.get("move_san"),
            "move_uci": item.get("move_uci"),
            "color": item.get("color"),
            "move_number": item.get("move_number"),
            "ply": item.get("ply"),
            "reason": item.get("reason"),
        }
        for item in items
    ]


def _public_leaf_unit(unit: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in unit.items() if key != "_lines"}


def _public_unit_lines(unit: dict[str, Any]) -> list[dict[str, Any]]:
    return list(unit.get("_lines") or [])


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
        variations_by_chapter[chapter.id] = list(await variation_repo.get_variations_for_chapter(chapter.id))

    return chapters, variations_by_chapter


async def _build_catalog(
    *,
    study_id: str,
    user_id: str,
    mode: OpeningTrainerMode,
    color: OpeningTrainerColor,
    node_service: NodeService,
    study_repo: StudyRepository,
    variation_repo: VariationRepository,
) -> dict[str, Any]:
    chapters, variations_by_chapter = await _load_study_context(
        study_id=study_id,
        user_id=user_id,
        node_service=node_service,
        study_repo=study_repo,
        variation_repo=variation_repo,
    )
    return build_unit_catalog(
        study_id=study_id,
        mode=mode.value,
        trainee_color=color.value,
        chapters=chapters,
        variations_by_chapter=variations_by_chapter,
    )


@router.get("/studies/{study_id}/eligibility", response_model=OpeningTrainerEligibilityResponse)
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


@router.get("/studies/{study_id}/units", response_model=OpeningTrainerUnitsResponse)
async def get_study_units(
    study_id: str,
    mode: OpeningTrainerMode = Query(default=OpeningTrainerMode.chapter),
    color: OpeningTrainerColor = Query(default=OpeningTrainerColor.white),
    user_id: str = Depends(get_workspace_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_workspace_study_repository),
    variation_repo: VariationRepository = Depends(get_workspace_variation_repository),
):
    catalog = await _build_catalog(
        study_id=study_id,
        user_id=user_id,
        mode=mode,
        color=color,
        node_service=node_service,
        study_repo=study_repo,
        variation_repo=variation_repo,
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


@router.get("/studies/{study_id}/units/{unit_id}", response_model=OpeningTrainerUnitDetailResponse)
async def get_unit_detail(
    study_id: str,
    unit_id: str,
    mode: OpeningTrainerMode = Query(default=OpeningTrainerMode.chapter),
    color: OpeningTrainerColor = Query(default=OpeningTrainerColor.white),
    user_id: str = Depends(get_workspace_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_workspace_study_repository),
    variation_repo: VariationRepository = Depends(get_workspace_variation_repository),
):
    catalog = await _build_catalog(
        study_id=study_id,
        user_id=user_id,
        mode=mode,
        color=color,
        node_service=node_service,
        study_repo=study_repo,
        variation_repo=variation_repo,
    )
    if not catalog["eligibility"]["eligible"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Study is not eligible for opening trainer",
                "reasons": catalog["eligibility"]["reasons"],
            },
        )

    leaf_unit = get_leaf_unit(catalog, unit_id)
    if not leaf_unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unit not found: {unit_id}")

    return {
        "study_id": study_id,
        "mode": mode.value,
        "color": color.value,
        "unit": _public_leaf_unit(leaf_unit),
        "lines": _public_unit_lines(leaf_unit),
    }


@router.post("/studies/{study_id}/train/start", response_model=OpeningTrainerTrainingStartResponse)
async def start_training(
    study_id: str,
    body: OpeningTrainerTrainingStartRequest,
    current_user: User = Depends(get_current_user),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_workspace_study_repository),
    variation_repo: VariationRepository = Depends(get_workspace_variation_repository),
    db: Session = Depends(get_opening_trainer_db),
):
    catalog = await _build_catalog(
        study_id=study_id,
        user_id=str(current_user.id),
        mode=body.mode,
        color=body.color,
        node_service=node_service,
        study_repo=study_repo,
        variation_repo=variation_repo,
    )
    if not catalog["eligibility"]["eligible"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Study is not eligible for opening trainer",
                "reasons": catalog["eligibility"]["reasons"],
            },
        )

    leaf_unit = get_leaf_unit(catalog, body.unit_id)
    if not leaf_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit not found: {body.unit_id}" if body.unit_id else "No trainable unit found",
        )

    line_pick = pick_line_for_unit(leaf_unit, body.seed)
    line_steps = line_pick["steps"]
    mastered_cache: dict[tuple[str, str, str], bool] = {}
    advance = advance_until_prompt(
        line_steps=line_steps,
        start_index=0,
        trainee_color=body.color.value,
        is_mastered=lambda step: _is_step_mastered(
            db=db,
            user_id=current_user.id,
            step=step,
            trainee_color=body.color.value,
            cache=mastered_cache,
        ),
    )

    session_payload = {
        "study_id": study_id,
        "mode": body.mode.value,
        "color": body.color.value,
        "training_mode": body.training_mode.value,
        "unit_id": leaf_unit["id"],
        "line_signature": line_pick["line_signature"],
        "line_index": line_pick["line_index"],
        "line_count": line_pick["line_count"],
        "step_index": advance["next_index"],
        "seed": line_pick["seed"],
    }
    return {
        "session": session_payload,
        "unit": _public_leaf_unit(leaf_unit),
        "auto_moves": _to_auto_moves(advance["auto_moves"]),
        "prompt": _to_prompt(advance["prompt"]),
        "finished": advance["finished"],
    }


@router.post("/studies/{study_id}/train/answer", response_model=OpeningTrainerTrainingAnswerResponse)
async def answer_training(
    study_id: str,
    body: OpeningTrainerTrainingAnswerRequest,
    current_user: User = Depends(get_current_user),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_workspace_study_repository),
    variation_repo: VariationRepository = Depends(get_workspace_variation_repository),
    db: Session = Depends(get_opening_trainer_db),
):
    session = body.session
    if session.study_id != study_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session study_id does not match path parameter",
        )

    catalog = await _build_catalog(
        study_id=study_id,
        user_id=str(current_user.id),
        mode=session.mode,
        color=session.color,
        node_service=node_service,
        study_repo=study_repo,
        variation_repo=variation_repo,
    )
    if not catalog["eligibility"]["eligible"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Study is not eligible for opening trainer",
                "reasons": catalog["eligibility"]["reasons"],
            },
        )

    leaf_unit = get_leaf_unit(catalog, session.unit_id)
    if not leaf_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit not found: {session.unit_id}",
        )

    line_steps = get_line_by_signature(leaf_unit, session.line_signature)
    if line_steps is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session line_signature is stale; restart session",
        )
    if session.step_index >= len(line_steps):
        return {
            "correct": True,
            "expected_move_san": "",
            "session": {
                **session.model_dump(),
                "step_index": len(line_steps),
            },
            "auto_moves": [],
            "prompt": None,
            "finished": True,
            "progress": None,
        }

    expected = line_steps[session.step_index]
    if expected.get("color") != session.color.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session step index is invalid; expected an auto-play move",
        )

    expected_san = expected.get("move_san", "")
    is_correct = normalize_san_for_compare(body.user_move_san) == normalize_san_for_compare(expected_san)
    progress_payload = None
    next_index = session.step_index
    auto_moves: list[dict[str, Any]] = []
    next_prompt: dict[str, Any] | None = expected
    finished = False

    if session.training_mode == OpeningTrainerTrainingMode.quiz:
        progress_row = _upsert_progress(
            db=db,
            user_id=current_user.id,
            from_fen=expected.get("from_fen", ""),
            move_san=expected_san,
            color=session.color.value,
            correct=is_correct,
        )
        progress_payload = _to_training_progress(progress_row)

    if is_correct:
        next_index += 1
        mastered_cache: dict[tuple[str, str, str], bool] = {}
        advance = advance_until_prompt(
            line_steps=line_steps,
            start_index=next_index,
            trainee_color=session.color.value,
            is_mastered=lambda step: _is_step_mastered(
                db=db,
                user_id=current_user.id,
                step=step,
                trainee_color=session.color.value,
                cache=mastered_cache,
            ),
        )
        next_index = advance["next_index"]
        auto_moves = _to_auto_moves(advance["auto_moves"])
        next_prompt = _to_prompt(advance["prompt"])
        finished = advance["finished"]
    else:
        next_prompt = _to_prompt(expected)

    return {
        "correct": is_correct,
        "expected_move_san": expected_san,
        "session": {
            **session.model_dump(),
            "step_index": next_index,
        },
        "auto_moves": auto_moves,
        "prompt": next_prompt,
        "finished": finished,
        "progress": progress_payload,
    }


@router.get("/progress", response_model=OpeningTrainerProgressListResponse)
def get_progress(
    fens_brackets: list[str] = Query(default_factory=list, alias="fens[]"),
    fens_plain: list[str] = Query(default_factory=list, alias="fens"),
    color: OpeningTrainerColor = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_opening_trainer_db),
):
    normalized_fens = _normalize_fen_list(fens_brackets, fens_plain)
    if not normalized_fens:
        return OpeningTrainerProgressListResponse(items=[])
    if len(normalized_fens) > MAX_PROGRESS_FENS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"fens size exceeds max limit ({MAX_PROGRESS_FENS})",
        )

    stmt = text(
        """
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
        """
    ).bindparams(bindparam("fens", expanding=True))

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

    return OpeningTrainerProgressListResponse(items=[_to_progress_item(row) for row in result])


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

    row = _upsert_progress(
        db=db,
        user_id=current_user.id,
        from_fen=from_fen,
        move_san=move_san,
        color=body.color.value,
        correct=body.correct,
    )
    return _to_progress_item(row)
