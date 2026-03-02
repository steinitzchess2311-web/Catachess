"""
Broadcast & Chat-link endpoints
================================
GET    /classrooms/{id}/chat                  Get catchat_group_id for frontend routing
POST   /classrooms/{id}/broadcast             Send announcement via catachat
GET    /classrooms/{id}/broadcasts            List broadcast messages (any member)
DELETE /classrooms/{id}/broadcasts/{mid}      Delete a broadcast (teacher+)
"""
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session as CatchatSession

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.schemas.classroom import (
    ChatLinkResponse, BroadcastCreate, BroadcastResponse, BroadcastItem,
)
from models.user import User

from .classrooms import _get_classroom_or_404, _my_role, _require_teacher

router = APIRouter(tags=["classroom-broadcasts"])


def _catchat_engine():
    return create_engine(os.getenv("CATCHAT_DATABASE"), pool_pre_ping=True)


# ── Chat link ────────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/chat", response_model=ChatLinkResponse)
def get_chat_link(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _my_role(classroom, current_user.username, db)
    return ChatLinkResponse(
        catchat_group_id=str(classroom.catchat_group_id) if classroom.catchat_group_id else None
    )


# ── Send broadcast ───────────────────────────────────────────────────────────

@router.post("/classrooms/{classroom_id}/broadcast", response_model=BroadcastResponse, status_code=201)
def broadcast(
    classroom_id: uuid.UUID,
    body: BroadcastCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)

    if not classroom.catchat_group_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Chat not available for this classroom")

    try:
        from modules.catchat.db.models.group_message import GroupMessage
        from modules.catchat.db.models.group import Group

        with CatchatSession(_catchat_engine()) as cdb:
            msg = GroupMessage(
                group_id=classroom.catchat_group_id,
                sender_id=current_user.id,
                sender_name=current_user.username,
                content=body.content,
                is_broadcast=True,
            )
            cdb.add(msg)
            # Update group's last_message_at so it surfaces in sidebar
            group = cdb.get(Group, classroom.catchat_group_id)
            if group:
                group.last_message_at = datetime.utcnow()
            cdb.commit()
            cdb.refresh(msg)
            return BroadcastResponse(
                broadcast_id=str(msg.id),
                created_at=msg.created_at,
            )
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Broadcast failed: {exc}")


# ── List broadcasts ──────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/broadcasts", response_model=list[BroadcastItem])
def list_broadcasts(
    classroom_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _my_role(classroom, current_user.username, db)   # any member can read

    if not classroom.catchat_group_id:
        return []

    try:
        from modules.catchat.db.models.group_message import GroupMessage

        with CatchatSession(_catchat_engine()) as cdb:
            rows = cdb.execute(
                select(GroupMessage)
                .where(
                    GroupMessage.group_id == classroom.catchat_group_id,
                    GroupMessage.is_broadcast.is_(True),
                )
                .order_by(desc(GroupMessage.created_at))
                .limit(limit)
            ).scalars().all()
            return [
                BroadcastItem(
                    broadcast_id=str(r.id),
                    sender_username=r.sender_name,
                    content=r.content,
                    created_at=r.created_at,
                )
                for r in rows
            ]
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Broadcasts unavailable: {exc}")


# ── Delete broadcast ─────────────────────────────────────────────────────────

@router.delete("/classrooms/{classroom_id}/broadcasts/{broadcast_id}", status_code=204)
def delete_broadcast(
    classroom_id: uuid.UUID,
    broadcast_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)

    if not classroom.catchat_group_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Chat not available")

    try:
        from modules.catchat.db.models.group_message import GroupMessage

        with CatchatSession(_catchat_engine()) as cdb:
            msg = cdb.execute(
                select(GroupMessage).where(
                    GroupMessage.id == broadcast_id,
                    GroupMessage.group_id == classroom.catchat_group_id,
                    GroupMessage.is_broadcast.is_(True),
                )
            ).scalar_one_or_none()
            if not msg:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Broadcast not found")
            cdb.delete(msg)
            cdb.commit()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Delete failed: {exc}")
