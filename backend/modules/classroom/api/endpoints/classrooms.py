"""
Classroom endpoints
===================
POST   /classrooms                    Create a classroom
GET    /classrooms                    List my classrooms
GET    /classrooms/{id}               Classroom detail
PATCH  /classrooms/{id}               Rename
DELETE /classrooms/{id}               Soft-delete (owner only)
POST   /classrooms/{id}/archive       Archive (owner only)
POST   /classrooms/{id}/unarchive     Restore from archive (owner only)
GET    /classrooms/{id}/invite        Get current invite code
POST   /classrooms/{id}/invite/reset  Refresh invite code
PATCH  /classrooms/{id}/invite        Enable/disable invite code
POST   /classrooms/join               Join via invite code
GET    /classrooms/{id}/chat          Get catchat_group_id for frontend routing
POST   /classrooms/{id}/broadcast     Send announcement via catachat
"""
import random
import string
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.schemas.classroom import (
    ClassroomCreate, ClassroomUpdate, ClassroomResponse, ClassroomListItem,
    InviteToggle, InviteResponse, JoinByCode, ChatLinkResponse,
    BroadcastCreate, BroadcastResponse,
)
from modules.classroom.services import catachat_sync, workspace_sync
from models.user import User

router = APIRouter(tags=["classroom-classrooms"])

_INVITE_CHARS = string.ascii_uppercase + string.digits


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gen_invite_code() -> str:
    return "".join(random.choices(_INVITE_CHARS, k=8))


def _get_classroom_or_404(db: Session, classroom_id: uuid.UUID) -> Classroom:
    c = db.get(Classroom, classroom_id)
    if not c or c.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return c


def _my_role(classroom: Classroom, username: str, db: Session) -> str:
    """Return 'owner', 'teacher', or 'student'. Raises 403 if not a member."""
    if classroom.owner == username:
        return "owner"
    member = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom.id,
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not a member of this classroom")
    return member.role


def _require_teacher(classroom: Classroom, username: str, db: Session) -> str:
    role = _my_role(classroom, username, db)
    if role not in ("owner", "teacher"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Teacher role required")
    return role


def _require_owner(classroom: Classroom, username: str) -> None:
    if classroom.owner != username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Owner role required")


def _member_count(db: Session, classroom_id: uuid.UUID) -> int:
    count = db.execute(
        select(func.count()).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one()
    # +1 for owner (not in members table)
    return (count or 0) + 1


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/classrooms", response_model=ClassroomResponse, status_code=201)
def create_classroom(
    body: ClassroomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = Classroom(
        name=body.name.strip(),
        owner=current_user.username,
        invite_code=_gen_invite_code(),
        invite_active=True,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    # Sync catachat group
    group_id = catachat_sync.sync_create_group(
        classroom_id=classroom.id,
        name=classroom.name,
        owner_user_id=str(current_user.id),
        owner_username=current_user.username,
    )
    if group_id:
        classroom.catchat_group_id = group_id
        db.commit()
        db.refresh(classroom)

    # Sync workspace: create shared folder in teacher's workspace
    ws_folder_id = workspace_sync.sync_create_classroom_folder(
        teacher_uuid=str(current_user.id),
        classroom_id=str(classroom.id),
        class_name=classroom.name,
    )
    if ws_folder_id:
        classroom.workspace_folder_id = ws_folder_id
        db.commit()
        db.refresh(classroom)

    return _to_response(classroom)


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/classrooms", response_model=list[ClassroomListItem])
def list_my_classrooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    username = current_user.username

    # Classrooms where I am owner
    owned = db.execute(
        select(Classroom).where(
            Classroom.owner == username,
            Classroom.deleted_at.is_(None),
        )
    ).scalars().all()

    # Classrooms where I am a member
    memberships = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalars().all()
    member_classroom_ids = [m.classroom_id for m in memberships]
    member_role_map = {m.classroom_id: m.role for m in memberships}

    member_classrooms = db.execute(
        select(Classroom).where(
            Classroom.id.in_(member_classroom_ids),
            Classroom.deleted_at.is_(None),
        )
    ).scalars().all() if member_classroom_ids else []

    result = []
    seen: set = set()

    for c in owned:
        seen.add(c.id)
        result.append(ClassroomListItem(
            id=str(c.id), name=c.name, owner=c.owner,
            my_role="owner",
            member_count=_member_count(db, c.id),
            archived_at=c.archived_at, created_at=c.created_at,
        ))

    for c in member_classrooms:
        if c.id in seen:
            continue
        result.append(ClassroomListItem(
            id=str(c.id), name=c.name, owner=c.owner,
            my_role=member_role_map.get(c.id, "student"),
            member_count=_member_count(db, c.id),
            archived_at=c.archived_at, created_at=c.created_at,
        ))

    result.sort(key=lambda x: x.created_at, reverse=True)
    return result


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}", response_model=ClassroomResponse)
def get_classroom(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _my_role(classroom, current_user.username, db)   # membership check
    return _to_response(classroom)


# ── Rename ────────────────────────────────────────────────────────────────────

@router.patch("/classrooms/{classroom_id}", response_model=ClassroomResponse)
def rename_classroom(
    classroom_id: uuid.UUID,
    body: ClassroomUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    classroom.name = body.name.strip()
    db.commit()
    catachat_sync.sync_rename_group(classroom.catchat_group_id, classroom.name)
    db.refresh(classroom)
    return _to_response(classroom)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/classrooms/{classroom_id}", status_code=204)
def delete_classroom(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_owner(classroom, current_user.username)
    catachat_sync.sync_dissolve_group(classroom.catchat_group_id)
    classroom.deleted_at = datetime.utcnow()
    db.commit()


# ── Archive / Unarchive ───────────────────────────────────────────────────────

@router.post("/classrooms/{classroom_id}/archive", response_model=ClassroomResponse)
def archive_classroom(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_owner(classroom, current_user.username)
    if not classroom.archived_at:
        classroom.archived_at = datetime.utcnow()
        db.commit()
    db.refresh(classroom)
    return _to_response(classroom)


@router.post("/classrooms/{classroom_id}/unarchive", response_model=ClassroomResponse)
def unarchive_classroom(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_owner(classroom, current_user.username)
    classroom.archived_at = None
    db.commit()
    db.refresh(classroom)
    return _to_response(classroom)


# ── Invite code ───────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/invite", response_model=InviteResponse)
def get_invite(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    return InviteResponse(invite_code=classroom.invite_code, invite_active=classroom.invite_active)


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


# ── Join via invite code ──────────────────────────────────────────────────────

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

    # Sync workspace: create student subfolder if classroom folder exists
    if classroom.workspace_folder_id:
        # Look up teacher UUID to generate JWT
        from models.user import User as UserModel
        from core.db.deps import get_db as get_main_db
        for main_db in get_main_db():
            teacher = main_db.execute(
                select(UserModel).where(UserModel.username == classroom.owner)
            ).scalar_one_or_none()
            if teacher:
                member_row = db.execute(
                    select(ClassroomMember).where(
                        ClassroomMember.classroom_id == classroom.id,
                        ClassroomMember.username == username,
                        ClassroomMember.removed_at.is_(None),
                    )
                ).scalar_one_or_none()
                ws_folder_id = workspace_sync.sync_create_student_folder(
                    teacher_uuid=str(teacher.id),
                    classroom_folder_id=classroom.workspace_folder_id,
                    student_username=username,
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
    )


# ── Chat link ─────────────────────────────────────────────────────────────────

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


# ── Broadcast ─────────────────────────────────────────────────────────────────

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

    # Write broadcast directly to catchat DB
    try:
        from modules.catchat.db.models.broadcast import Broadcast
        from modules.catchat.db.session import Base  # noqa
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session as CatchatSession
        import os

        engine = create_engine(os.getenv("CATCHAT_DATABASE"), pool_pre_ping=True)
        with CatchatSession(engine) as cdb:
            broadcast_obj = Broadcast(
                group_id=classroom.catchat_group_id,
                sender_id=current_user.id,
                content=body.content,
            )
            cdb.add(broadcast_obj)
            cdb.commit()
            cdb.refresh(broadcast_obj)
            return BroadcastResponse(
                broadcast_id=str(broadcast_obj.id),
                created_at=broadcast_obj.created_at,
            )
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Broadcast failed: {exc}")


# ── Serialisation helper ──────────────────────────────────────────────────────

def _to_response(c: Classroom) -> ClassroomResponse:
    return ClassroomResponse(
        id=str(c.id),
        name=c.name,
        owner=c.owner,
        invite_code=c.invite_code,
        invite_active=c.invite_active,
        catchat_group_id=str(c.catchat_group_id) if c.catchat_group_id else None,
        workspace_folder_id=c.workspace_folder_id,
        created_at=c.created_at,
        archived_at=c.archived_at,
    )
