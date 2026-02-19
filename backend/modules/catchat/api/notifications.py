"""
Notification endpoint
=====================
GET /notifications   — last N messages received across all the user's conversations
                       (i.e. sent by someone else, not the current user)

Used by the catachess header bell-icon to show a quick preview.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from modules.catchat.auth import get_current_user
from modules.catchat.db.session import get_db
from modules.catchat.db.models import Conversation, Message
from modules.catchat.schemas import MessageResponse
from models.user import User

router = APIRouter(prefix="/notifications", tags=["catchat"])


@router.get("", response_model=list[MessageResponse])
def get_notifications(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id
    # Fetch a larger batch so we can deduplicate by sender
    rows = db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            or_(Conversation.user1_id == uid, Conversation.user2_id == uid),
            Message.sender_id != uid,
        )
        .order_by(Message.created_at.desc())
        .limit(limit * 20)
    ).scalars().all()

    # Keep only the latest message per sender
    seen_senders: set = set()
    unique: list = []
    for m in rows:
        if m.sender_id not in seen_senders:
            seen_senders.add(m.sender_id)
            unique.append(m)
            if len(unique) == limit:
                break

    return [
        MessageResponse(
            id=str(m.id),
            conversation_id=str(m.conversation_id),
            sender_id=str(m.sender_id),
            sender_name=m.sender_name,
            content=m.content,
            created_at=m.created_at,
        )
        for m in unique
    ]
