"""
Message endpoints
=================
GET  /conversations/{conv_id}/messages   — paginated history (newest first)
POST /conversations/{conv_id}/messages   — send a message

Pagination: use ?before=<ISO datetime> to load older pages.
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.catchat.auth import get_current_user
from modules.catchat.db.session import get_db
from modules.catchat.db.models import Conversation, Message
from modules.catchat.schemas import MessageCreate, MessageResponse
from models.user import User

router = APIRouter(prefix="/conversations", tags=["catchat"])


def _get_conv_or_404(conv_id: str, db: Session) -> Conversation:
    try:
        cid = uuid.UUID(conv_id)
    except ValueError:
        raise HTTPException(400, "Invalid conversation ID")
    conv = db.get(Conversation, cid)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv


def _assert_member(conv: Conversation, uid: uuid.UUID) -> None:
    if conv.user1_id != uid and conv.user2_id != uid:
        raise HTTPException(403, "Not a member of this conversation")


@router.get("/{conv_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conv_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = Query(None, description="ISO datetime cursor (exclusive)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_conv_or_404(conv_id, db)
    _assert_member(conv, current_user.id)

    q = select(Message).where(Message.conversation_id == conv.id)
    if before:
        try:
            q = q.where(Message.created_at < datetime.fromisoformat(before))
        except ValueError:
            raise HTTPException(400, "Invalid 'before' datetime — use ISO format")

    rows = db.execute(
        q.order_by(Message.created_at.desc()).limit(limit)
    ).scalars().all()

    return [
        MessageResponse(
            id=str(m.id), conversation_id=str(m.conversation_id),
            sender_id=str(m.sender_id), sender_name=m.sender_name,
            content=m.content, created_at=m.created_at,
        )
        for m in rows
    ]


@router.post("/{conv_id}/messages", response_model=MessageResponse, status_code=201)
def send_message(
    conv_id: str,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_conv_or_404(conv_id, db)
    _assert_member(conv, current_user.id)

    msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        sender_name=current_user.username,
        content=body.content,
    )
    db.add(msg)
    conv.last_message_at = datetime.utcnow()  # bump conversation to top of list
    db.commit()
    db.refresh(msg)

    return MessageResponse(
        id=str(msg.id), conversation_id=str(msg.conversation_id),
        sender_id=str(msg.sender_id), sender_name=msg.sender_name,
        content=msg.content, created_at=msg.created_at,
    )
