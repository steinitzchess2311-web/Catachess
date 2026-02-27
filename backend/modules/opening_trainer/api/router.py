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
from modules.opening_trainer.schemas import (
    OpeningTrainerColor,
    OpeningTrainerProgressItem,
    OpeningTrainerProgressListResponse,
    OpeningTrainerProgressUpsertRequest,
)

router = APIRouter(prefix="/api/v1/opening-trainer", tags=["opening-trainer"])


@router.get("/progress", response_model=OpeningTrainerProgressListResponse)
def get_progress(
    fens: list[str] = Query(default_factory=list, alias="fens[]"),
    color: OpeningTrainerColor = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_opening_trainer_db),
):
    if not fens:
        return OpeningTrainerProgressListResponse(items=[])

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
                "fens": fens,
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
        "from_fen": body.from_fen,
        "move_san": body.move_san,
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

