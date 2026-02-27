"""
Group message endpoints
=======================
GET  /groups/{group_id}/messages?limit=50   Fetch messages (newest last after reverse)
POST /groups/{group_id}/messages            Send a message (any group member)

Kept separate from groups.py so group CRUD logic and message logic
don't mix in the same file.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.catchat.auth import get_current_user
from modules.catchat.db.session import get_db
from modules.catchat.db.models.group import Group
from modules.catchat.db.models.group_member import GroupMember
from modules.catchat.db.models.group_message import GroupMessage
from modules.catchat.schemas.group import GroupMessageCreate, GroupMessageResponse
from models.user import User

router = APIRouter(prefix="/groups", tags=["catchat-group-messages"])
ANNOUNCEMENT_PLACEHOLDER = "[📢ANNOUNCEMENT📢]"


def _get_membership_or_403(
    db: Session, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMember:
    m = db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not a member of this group")
    return m


@router.get("/{group_id}/messages", response_model=list[GroupMessageResponse])
def get_group_messages(
    group_id: uuid.UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_membership_or_403(db, group_id, current_user.id)

    msgs = db.execute(
        select(GroupMessage)
        .where(GroupMessage.group_id == group_id)
        .order_by(GroupMessage.created_at.desc())
        .limit(limit)
    ).scalars().all()

    return [
        GroupMessageResponse(
            id=str(m.id),
            group_id=str(m.group_id),
            sender_id=str(m.sender_id),
            sender_name=m.sender_name,
            content=ANNOUNCEMENT_PLACEHOLDER if m.is_broadcast else m.content,
            created_at=m.created_at,
        )
        for m in msgs
    ]


@router.post("/{group_id}/messages", response_model=GroupMessageResponse, status_code=201)
def send_group_message(
    group_id: uuid.UUID,
    body: GroupMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_membership_or_403(db, group_id, current_user.id)

    now = datetime.utcnow()
    msg = GroupMessage(
        group_id=group_id,
        sender_id=current_user.id,
        sender_name=current_user.username or str(current_user.id)[:8],
        content=body.content,
        created_at=now,
    )
    db.add(msg)

    # Update last_message_at so the group floats to the top of the sidebar
    group = db.get(Group, group_id)
    if group:
        group.last_message_at = now

    db.commit()
    db.refresh(msg)

    return GroupMessageResponse(
        id=str(msg.id),
        group_id=str(msg.group_id),
        sender_id=str(msg.sender_id),
        sender_name=msg.sender_name,
        content=msg.content,
        created_at=msg.created_at,
    )
