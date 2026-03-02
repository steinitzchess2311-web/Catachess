"""
Contact Teacher endpoint
========================
POST   /classrooms/{id}/contact-teacher   Open/create private or group chat with teacher(s)

Student-only. For classrooms with 1 teacher, creates a private CataChat
conversation. For multiple teachers, creates a group chat with all teachers
and the student. Idempotent — returns existing chat if one already exists.
"""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session as CatchatSession

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.schemas.classroom import ContactTeacherResponse
from models.user import User

from .classrooms import _get_classroom_or_404, _my_role, _resolve_user_uuid

router = APIRouter(tags=["classroom-contact"])


@router.post("/classrooms/{classroom_id}/contact-teacher", response_model=ContactTeacherResponse)
def contact_teacher(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or retrieve a private/group chat between student and classroom teachers."""
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    if role not in ("student",):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Student role required")

    # Collect all teacher usernames (owner + teacher-role members)
    teacher_usernames = [classroom.owner]
    teacher_members = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom.id,
            ClassroomMember.role == "teacher",
            ClassroomMember.removed_at.is_(None),
        )
    ).scalars().all()
    for m in teacher_members:
        if m.username not in teacher_usernames:
            teacher_usernames.append(m.username)

    # Resolve teacher UUIDs from main DB
    teacher_ids: list[tuple[str, uuid.UUID]] = []
    for uname in teacher_usernames:
        uid = _resolve_user_uuid(uname)
        if uid:
            teacher_ids.append((uname, uuid.UUID(uid)))

    if not teacher_ids:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not resolve teacher accounts")

    engine = create_engine(os.getenv("CATCHAT_DATABASE"), pool_pre_ping=True)

    try:
        with CatchatSession(engine) as cdb:
            student_id = current_user.id

            if len(teacher_ids) == 1:
                return _open_private_conversation(cdb, student_id, teacher_ids[0][1])
            else:
                return _open_group_chat(cdb, student_id, current_user.username, teacher_ids, classroom.name)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Chat service error: {exc}")


# ── Private conversation (1 teacher) ─────────────────────────────────────────

def _open_private_conversation(
    cdb: CatchatSession,
    student_id: uuid.UUID,
    teacher_id: uuid.UUID,
) -> ContactTeacherResponse:
    """Create or retrieve a 1-on-1 conversation using sorted-pair upsert."""
    from modules.catchat.db.models.conversation import Conversation

    u1, u2 = (student_id, teacher_id) if student_id < teacher_id else (teacher_id, student_id)

    conv = cdb.execute(
        select(Conversation).where(
            and_(Conversation.user1_id == u1, Conversation.user2_id == u2)
        )
    ).scalar_one_or_none()

    if not conv:
        conv = Conversation(user1_id=u1, user2_id=u2)
        cdb.add(conv)
        cdb.commit()
        cdb.refresh(conv)

    return ContactTeacherResponse(chat_type="conversation", chat_id=str(conv.id))


# ── Group chat (multiple teachers) ───────────────────────────────────────────

def _open_group_chat(
    cdb: CatchatSession,
    student_id: uuid.UUID,
    student_username: str,
    teacher_ids: list[tuple[str, uuid.UUID]],
    classroom_name: str,
) -> ContactTeacherResponse:
    """Create or retrieve a group chat with the student and all teachers."""
    from modules.catchat.db.models.group import Group
    from modules.catchat.db.models.group_member import GroupMember

    all_user_ids = sorted([student_id] + [tid for _, tid in teacher_ids])

    # Look for existing group with exactly these members
    existing_groups = cdb.execute(
        select(GroupMember.group_id)
        .where(GroupMember.user_id.in_(all_user_ids))
        .group_by(GroupMember.group_id)
        .having(func.count() == len(all_user_ids))
    ).scalars().all()

    for gid in existing_groups:
        # Verify exact match (no extra members)
        member_count = cdb.execute(
            select(func.count()).where(GroupMember.group_id == gid)
        ).scalar_one()
        if member_count == len(all_user_ids):
            return ContactTeacherResponse(chat_type="group", chat_id=str(gid))

    # Create new group
    group = Group(
        name=f"{classroom_name} — Contact",
        created_by=student_id,
    )
    cdb.add(group)
    cdb.flush()

    # Add student
    cdb.add(GroupMember(
        group_id=group.id,
        user_id=student_id,
        username=student_username,
        role="member",
    ))
    # Add teachers
    for uname, tid in teacher_ids:
        cdb.add(GroupMember(
            group_id=group.id,
            user_id=tid,
            username=uname,
            role="admin",
        ))

    cdb.commit()
    cdb.refresh(group)
    return ContactTeacherResponse(chat_type="group", chat_id=str(group.id))
