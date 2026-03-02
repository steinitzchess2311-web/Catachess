"""
Invite & Join endpoints
=======================
GET    /classrooms/{id}/invite        Get current invite code
POST   /classrooms/{id}/invite/reset  Refresh invite code
PATCH  /classrooms/{id}/invite        Enable/disable invite code
POST   /classrooms/join               Join via invite code
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.schemas.classroom import (
    InviteToggle, InviteResponse, JoinByCode, ClassroomListItem,
)
from modules.classroom.services import catachat_sync, workspace_sync
from models.user import User

from .classrooms import (
    _get_classroom_or_404, _require_teacher, _gen_invite_code, _member_count,
)

router = APIRouter(tags=["classroom-invites"])


# ── Get invite code ──────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/invite", response_model=InviteResponse)
def get_invite(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    return InviteResponse(invite_code=classroom.invite_code, invite_active=classroom.invite_active)


# ── Reset invite code ────────────────────────────────────────────────────────

@router.post("/classrooms/{classroom_id}/invite/reset", response_model=InviteResponse)
def reset_invite(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    classroom.invite_code = _gen_invite_code()
    db.commit()
    return InviteResponse(invite_code=classroom.invite_code, invite_active=classroom.invite_active)


# ── Toggle invite ────────────────────────────────────────────────────────────

@router.patch("/classrooms/{classroom_id}/invite", response_model=InviteResponse)
def toggle_invite(
    classroom_id: uuid.UUID,
    body: InviteToggle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    classroom.invite_active = body.active
    db.commit()
    return InviteResponse(invite_code=classroom.invite_code, invite_active=classroom.invite_active)


# ── Join via invite code ─────────────────────────────────────────────────────

@router.post("/classrooms/join", response_model=ClassroomListItem, status_code=201)
def join_classroom(
    body: JoinByCode,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = db.execute(
        select(Classroom).where(
            Classroom.invite_code == body.invite_code.upper(),
            Classroom.invite_active.is_(True),
            Classroom.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if not classroom:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invalid or inactive invite code")

    username = current_user.username

    # Owner trying to join their own classroom
    if classroom.owner == username:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="You are the owner of this classroom")

    # Check if already a member (active or removed)
    existing = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom.id,
            ClassroomMember.username == username,
        )
    ).scalar_one_or_none()

    if existing:
        if existing.removed_at is None:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Already a member")
        # Re-join: restore the row
        existing.removed_at = None
        existing.role = "student"
        db.commit()
    else:
        db.add(ClassroomMember(
            classroom_id=classroom.id,
            username=username,
            role="student",
        ))
        db.commit()

    catachat_sync.sync_add_member(
        classroom.catchat_group_id,
        user_id=str(current_user.id),
        username=username,
        classroom_role="student",
    )

    # Sync workspace: get or create student subfolder under 'My Classroom/'.
    # If the student is already in another classroom of the same teacher,
    # reuse their existing folder rather than creating a duplicate.
    if classroom.workspace_folder_id:
        from models.user import User as UserModel
        from core.db.deps import get_db as get_main_db
        for main_db in get_main_db():
            teacher = main_db.execute(
                select(UserModel).where(UserModel.username == classroom.owner)
            ).scalar_one_or_none()
            if teacher:
                # Check if this student already has a folder under this teacher
                existing_student_folder = db.execute(
                    select(ClassroomMember.workspace_folder_id)
                    .join(Classroom, ClassroomMember.classroom_id == Classroom.id)
                    .where(
                        Classroom.owner == classroom.owner,
                        Classroom.deleted_at.is_(None),
                        ClassroomMember.username == username,
                        ClassroomMember.workspace_folder_id.is_not(None),
                        ClassroomMember.removed_at.is_(None),
                    )
                    .limit(1)
                ).scalar_one_or_none()

                member_row = db.execute(
                    select(ClassroomMember).where(
                        ClassroomMember.classroom_id == classroom.id,
                        ClassroomMember.username == username,
                        ClassroomMember.removed_at.is_(None),
                    )
                ).scalar_one_or_none()

                ws_folder_id = workspace_sync.sync_get_or_create_student_folder(
                    teacher_uuid=str(teacher.id),
                    root_folder_id=classroom.workspace_folder_id,
                    student_username=username,
                    existing_student_folder_id=existing_student_folder,
                )
                if ws_folder_id and member_row:
                    member_row.workspace_folder_id = ws_folder_id
                    db.commit()
            break

    return ClassroomListItem(
        id=str(classroom.id), name=classroom.name, owner=classroom.owner,
        my_role="student",
        member_count=_member_count(db, classroom.id),
        archived_at=classroom.archived_at, created_at=classroom.created_at,
        workspace_folder_id=classroom.workspace_folder_id,
    )
