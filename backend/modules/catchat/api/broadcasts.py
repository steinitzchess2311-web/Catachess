"""
Broadcast endpoints
===================
GET  /broadcasts   — list broadcasts (all authenticated users)
POST /broadcasts   — send a broadcast (admin only)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.catchat.auth import get_current_user, require_admin
from modules.catchat.db.session import get_db
from modules.catchat.db.models import Broadcast
from modules.catchat.schemas import BroadcastCreate, BroadcastResponse
from models.user import User

router = APIRouter(prefix="/broadcasts", tags=["catchat"])


@router.get("", response_model=list[BroadcastResponse])
def list_broadcasts(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Broadcast).order_by(Broadcast.created_at.desc()).limit(limit)
    ).scalars().all()

    return [
        BroadcastResponse(
            id=str(b.id), sender_id=str(b.sender_id),
            sender_name=b.sender_name, content=b.content,
            created_at=b.created_at,
        )
        for b in rows
    ]


@router.post("", response_model=BroadcastResponse, status_code=201)
def send_broadcast(
    body: BroadcastCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    b = Broadcast(
        sender_id=current_user.id,
        sender_name=current_user.username or "Admin",
        content=body.content,
    )
    db.add(b)
    db.commit()
    db.refresh(b)

    return BroadcastResponse(
        id=str(b.id), sender_id=str(b.sender_id),
        sender_name=b.sender_name, content=b.content,
        created_at=b.created_at,
    )
