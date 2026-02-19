"""
Conversation endpoints
======================
GET  /conversations        — list my conversations, sorted by most recent message
POST /conversations        — open (or retrieve existing) conversation with a user
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from modules.catchat.auth import get_current_user
from modules.catchat.db.session import get_db
from modules.catchat.db.models import Conversation
from modules.catchat.schemas import ConversationCreate, ConversationResponse
from models.user import User

router = APIRouter(prefix="/conversations", tags=["catchat"])


def _sorted_pair(a: uuid.UUID, b: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    """Ensure user1_id < user2_id to satisfy the unique-pair constraint."""
    return (a, b) if a < b else (b, a)


@router.get("", response_model=list[ConversationResponse])
def list_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id
    rows = db.execute(
        select(Conversation)
        .where(or_(Conversation.user1_id == uid, Conversation.user2_id == uid))
        .order_by(Conversation.last_message_at.desc())
    ).scalars().all()

    return [
        ConversationResponse(
            id=str(c.id),
            other_user_id=str(c.user2_id if c.user1_id == uid else c.user1_id),
            last_message_at=c.last_message_at,
            created_at=c.created_at,
        )
        for c in rows
    ]


@router.post("", response_model=ConversationResponse, status_code=201)
def open_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        other_id = uuid.UUID(body.user_id)
    except ValueError:
        raise HTTPException(400, "Invalid user_id — must be a UUID string")

    if other_id == current_user.id:
        raise HTTPException(400, "Cannot start a conversation with yourself")

    u1, u2 = _sorted_pair(current_user.id, other_id)
    conv = db.execute(
        select(Conversation).where(
            and_(Conversation.user1_id == u1, Conversation.user2_id == u2)
        )
    ).scalar_one_or_none()

    if not conv:
        conv = Conversation(user1_id=u1, user2_id=u2)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    return ConversationResponse(
        id=str(conv.id),
        other_user_id=str(other_id),
        last_message_at=conv.last_message_at,
        created_at=conv.created_at,
    )
