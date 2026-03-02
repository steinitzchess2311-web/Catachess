"""
Classroom CRUD endpoints (integration file)
============================================
POST   /classrooms                    Create a classroom
GET    /classrooms                    List my classrooms
GET    /classrooms/{id}               Classroom detail
PATCH  /classrooms/{id}               Rename
DELETE /classrooms/{id}               Soft-delete (owner only)
POST   /classrooms/{id}/archive       Archive (owner only)
POST   /classrooms/{id}/unarchive     Restore from archive (owner only)

Shared helpers exported for use by sibling endpoint modules:
  _get_classroom_or_404, _my_role, _require_teacher, _require_owner,
  _member_count, _batch_member_counts, _gen_invite_code, _to_response,
  _resolve_user_uuid

Related endpoint modules (registered separately in router.py):
  invites.py      — invite code management + join
  broadcasts.py   — chat link, broadcast send/list/delete
  contact.py      — contact-teacher (student→teacher chat)
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
)
from modules.classroom.services import catachat_sync, workspace_sync
from models.user import User

router = APIRouter(tags=["classroom-classrooms"])

_INVITE_CHARS = string.ascii_uppercase + string.digits


# ── Shared helpers ───────────────────────────────────────────────────────────
# These are imported by invites.py, broadcasts.py, contact.py, etc.

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


def _batch_member_counts(db: Session, classroom_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    """Single GROUP BY query for member counts across multiple classrooms."""
    if not classroom_ids:
        return {}
    rows = db.execute(
        select(ClassroomMember.classroom_id, func.count().label("cnt"))
        .where(
            ClassroomMember.classroom_id.in_(classroom_ids),
            ClassroomMember.removed_at.is_(None),
        )
        .group_by(ClassroomMember.classroom_id)
    ).all()
    counts = {row.classroom_id: row.cnt for row in rows}
    # +1 for owner (not in members table)
    return {cid: counts.get(cid, 0) + 1 for cid in classroom_ids}


def _resolve_user_uuid(username: str) -> str | None:
    """Resolve a username to UUID from the main DB."""
    from core.db.deps import get_db as get_main_db
    for main_db in get_main_db():
        user = main_db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if user:
            return str(user.id)
        break
    return None


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


# ── Create ───────────────────────────────────────────────────────────────────

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

    # Sync workspace: get or create 'My Classroom/' root folder for this teacher.
    # All classrooms owned by the same teacher share one root folder.
    existing_root = db.execute(
        select(Classroom).where(
            Classroom.owner == current_user.username,
            Classroom.workspace_folder_id.is_not(None),
            Classroom.deleted_at.is_(None),
            Classroom.id != classroom.id,
        ).limit(1)
    ).scalar_one_or_none()

    ws_root_id = workspace_sync.sync_get_or_create_root_folder(
        teacher_uuid=str(current_user.id),
        existing_root_folder_id=existing_root.workspace_folder_id if existing_root else None,
    )
    if ws_root_id:
        classroom.workspace_folder_id = ws_root_id
        db.commit()
        db.refresh(classroom)

    return _to_response(classroom)


# ── List ─────────────────────────────────────────────────────────────────────

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

    # Batch member counts — one GROUP BY query instead of N individual queries
    all_classroom_ids = list({c.id for c in list(owned) + list(member_classrooms)})
    member_counts = _batch_member_counts(db, all_classroom_ids)

    result = []
    seen: set = set()

    for c in owned:
        seen.add(c.id)
        result.append(ClassroomListItem(
            id=str(c.id), name=c.name, owner=c.owner,
            my_role="owner",
            member_count=member_counts.get(c.id, 1),
            archived_at=c.archived_at, created_at=c.created_at,
            workspace_folder_id=c.workspace_folder_id,
        ))

    for c in member_classrooms:
        if c.id in seen:
            continue
        result.append(ClassroomListItem(
            id=str(c.id), name=c.name, owner=c.owner,
            my_role=member_role_map.get(c.id, "student"),
            member_count=member_counts.get(c.id, 1),
            archived_at=c.archived_at, created_at=c.created_at,
            workspace_folder_id=c.workspace_folder_id,
        ))

    result.sort(key=lambda x: x.created_at, reverse=True)
    return result


# ── Detail ───────────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}", response_model=ClassroomResponse)
def get_classroom(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _my_role(classroom, current_user.username, db)   # membership check
    return _to_response(classroom)


# ── Rename ───────────────────────────────────────────────────────────────────

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


# ── Delete ───────────────────────────────────────────────────────────────────

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


# ── Archive / Unarchive ──────────────────────────────────────────────────────

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
