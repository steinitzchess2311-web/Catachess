"""
Member endpoints
================
GET    /classrooms/{id}/members                   Member list (any member)
POST   /classrooms/{id}/members                   Add member (teacher+)
DELETE /classrooms/{id}/members/{username}        Remove member (teacher+)
PATCH  /classrooms/{id}/members/{username}/role   Change role (owner only)
POST   /classrooms/{id}/members/leave             Leave classroom (student/teacher)
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.schemas.member import MemberAdd, MemberRoleUpdate, MemberResponse, FolderRename
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.services import catachat_sync, workspace_sync
from models.user import User

router = APIRouter(tags=["classroom-members"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_classroom_or_404(db: Session, classroom_id: uuid.UUID) -> Classroom:
    c = db.get(Classroom, classroom_id)
    if not c or c.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return c


def _my_role(classroom: Classroom, username: str, db: Session) -> str:
    if classroom.owner == username:
        return "owner"
    m = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom.id,
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not a member of this classroom")
    return m.role


def _require_teacher(classroom: Classroom, username: str, db: Session) -> None:
    if _my_role(classroom, username, db) not in ("owner", "teacher"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Teacher role required")


def _require_owner(classroom: Classroom, username: str) -> None:
    if classroom.owner != username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Owner role required")


# ── List members ──────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/members", response_model=list[MemberResponse])
def list_members(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _my_role(classroom, current_user.username, db)   # membership check

    members = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.removed_at.is_(None),
        ).order_by(ClassroomMember.joined_at)
    ).scalars().all()

    # Prepend owner as a synthetic entry
    result = [
        MemberResponse(
            username=classroom.owner,
            role="owner",
            invited_by=None,
            joined_at=classroom.created_at,
        )
    ]
    for m in members:
        result.append(MemberResponse(
            username=m.username,
            role=m.role,
            invited_by=m.invited_by,
            joined_at=m.joined_at,
        ))
    return result


# ── Add member ────────────────────────────────────────────────────────────────

@router.post("/classrooms/{classroom_id}/members", response_model=MemberResponse, status_code=201)
def add_member(
    classroom_id: uuid.UUID,
    body: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)

    if body.username == classroom.owner:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User is the owner of this classroom")

    existing = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.username == body.username,
        )
    ).scalar_one_or_none()

    if existing:
        if existing.removed_at is None:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="User is already a member")
        # Re-add: restore row with new role
        existing.removed_at = None
        existing.role = body.role
        existing.invited_by = current_user.username
        existing.joined_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        member = existing
    else:
        member = ClassroomMember(
            classroom_id=classroom_id,
            username=body.username,
            role=body.role,
            invited_by=current_user.username,
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    catachat_sync.sync_add_member(
        classroom.catchat_group_id,
        user_id=body.user_id,
        username=body.username,
        classroom_role=body.role,
    )

    # Sync workspace: get or create student subfolder under 'My Classroom/'.
    # Reuse existing folder if the student is already in another classroom
    # of the same teacher, to avoid duplicate folders.
    if classroom.workspace_folder_id:
        from models.user import User as UserModel
        from core.db.deps import get_db as get_main_db
        for main_db in get_main_db():
            teacher = main_db.execute(
                select(UserModel).where(UserModel.username == classroom.owner)
            ).scalar_one_or_none()
            if teacher:
                existing_student_folder = db.execute(
                    select(ClassroomMember.workspace_folder_id)
                    .join(Classroom, ClassroomMember.classroom_id == Classroom.id)
                    .where(
                        Classroom.owner == classroom.owner,
                        Classroom.deleted_at.is_(None),
                        ClassroomMember.username == body.username,
                        ClassroomMember.workspace_folder_id.is_not(None),
                        ClassroomMember.removed_at.is_(None),
                    )
                    .limit(1)
                ).scalar_one_or_none()

                ws_folder_id = workspace_sync.sync_get_or_create_student_folder(
                    teacher_uuid=str(teacher.id),
                    root_folder_id=classroom.workspace_folder_id,
                    student_username=body.username,
                    existing_student_folder_id=existing_student_folder,
                )
                if ws_folder_id:
                    member.workspace_folder_id = ws_folder_id
                    db.commit()
            break

    return MemberResponse(
        username=member.username,
        role=member.role,
        invited_by=member.invited_by,
        joined_at=member.joined_at,
    )


# ── Remove member ─────────────────────────────────────────────────────────────

@router.delete("/classrooms/{classroom_id}/members/{username}", status_code=204)
def remove_member(
    classroom_id: uuid.UUID,
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)

    if username == classroom.owner:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot remove the classroom owner")

    member = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Teachers cannot remove other teachers (owner only)
    if member.role == "teacher" and classroom.owner != current_user.username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only the owner can remove a teacher")

    # Look up user_id from main DB for catachat sync
    from models.user import User as UserModel
    from core.db.deps import get_db as get_main_db
    target_user = None
    try:
        from sqlalchemy import select as sa_select
        for main_db in get_main_db():
            target_user = main_db.execute(
                sa_select(UserModel).where(UserModel.username == username)
            ).scalar_one_or_none()
            break
    except Exception:
        pass

    member.removed_at = datetime.utcnow()
    db.commit()

    if target_user:
        catachat_sync.sync_remove_member(classroom.catchat_group_id, str(target_user.id))


# ── Change role ───────────────────────────────────────────────────────────────

@router.patch("/classrooms/{classroom_id}/members/{username}/role", response_model=MemberResponse)
def change_role(
    classroom_id: uuid.UUID,
    username: str,
    body: MemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_owner(classroom, current_user.username)

    if username == classroom.owner:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot change the owner's role")

    member = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")

    member.role = body.role
    db.commit()

    # Look up user_id for catachat sync
    try:
        from models.user import User as UserModel
        from core.db.deps import get_db as get_main_db
        for main_db in get_main_db():
            target = main_db.execute(
                select(UserModel).where(UserModel.username == username)
            ).scalar_one_or_none()
            if target:
                catachat_sync.sync_update_role(
                    classroom.catchat_group_id, str(target.id), body.role
                )
            break
    except Exception:
        pass

    db.refresh(member)
    return MemberResponse(
        username=member.username, role=member.role,
        invited_by=member.invited_by, joined_at=member.joined_at,
    )


# ── Leave ─────────────────────────────────────────────────────────────────────

@router.post("/classrooms/{classroom_id}/members/leave", status_code=204)
def leave_classroom(
    classroom_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    username = current_user.username

    if classroom.owner == username:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot leave. Transfer ownership or delete the classroom.",
        )

    member = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not a member of this classroom")

    member.removed_at = datetime.utcnow()
    db.commit()

    catachat_sync.sync_remove_member(classroom.catchat_group_id, str(current_user.id))


# ── Rename student workspace folder ───────────────────────────────────────────

@router.patch("/classrooms/{classroom_id}/members/{username}/folder", status_code=204)
def rename_student_folder(
    classroom_id: uuid.UUID,
    username: str,
    body: FolderRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Rename a student's workspace folder (e.g. username → real name).
    Only changes the workspace folder title; classroom DB is not affected.
    Requires teacher+ role.
    """
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)

    member = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")
    if not member.workspace_folder_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No workspace folder for this member")

    # Look up teacher UUID to generate workspace JWT
    from models.user import User as UserModel
    from core.db.deps import get_db as get_main_db
    teacher_uuid = None
    for main_db in get_main_db():
        teacher = main_db.execute(
            select(UserModel).where(UserModel.username == classroom.owner)
        ).scalar_one_or_none()
        if teacher:
            teacher_uuid = str(teacher.id)
        break

    if not teacher_uuid:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Teacher not found")

    ok = workspace_sync.sync_rename_student_folder(
        teacher_uuid=teacher_uuid,
        folder_node_id=member.workspace_folder_id,
        new_title=body.title,
    )
    if not ok:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Workspace rename failed")
