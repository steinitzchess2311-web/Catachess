"""
Classroom Workspace Share endpoint
====================================
POST /classrooms/{id}/share-to-teacher

Allows a student to share one of their own workspace nodes (study or folder)
directly with the classroom's teacher via the classroom UI.

Mechanism:
  - Pure ACL share (same as normal workspace share).
  - The node stays in the student's private workspace; the student keeps full
    edit access and can continue working on it normally.
  - The teacher receives 'viewer' ACL on the node and sees it appear in their
    workspace Shared section in real-time.
  - inherit_to_children=True: for studies, all chapters are also visible.

This differs from the legacy /api/v1/workspace/share endpoint only in context:
  - Trigger: classroom UI "Share to Teacher" button (not workspace UI)
  - Auth: validated as classroom member; teacher UUID resolved from classroom record
  - The student does not need to know the teacher's username/id
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.services import workspace_sync
from models.user import User

router = APIRouter(tags=["classroom-shares"])


# ── Schema ────────────────────────────────────────────────────────────────────

class ShareToTeacherRequest(BaseModel):
    node_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Workspace node ID (study or folder) to share with the teacher.",
    )


class ShareToTeacherResponse(BaseModel):
    ok: bool
    message: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_classroom_or_404(db: Session, classroom_id: uuid.UUID) -> Classroom:
    c = db.get(Classroom, classroom_id)
    if not c or c.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return c


def _require_student_member(classroom: Classroom, username: str, db: Session) -> None:
    """Validate the caller is an active student (not owner/teacher) in this classroom."""
    if classroom.owner == username:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Owners do not share to themselves.",
        )
    member = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom.id,
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Not a member of this classroom.",
        )
    # Teachers can also share to the classroom owner; restrict to student only
    if member.role not in ("student",):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only students can use Share to Teacher.",
        )


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/classrooms/{classroom_id}/share-to-teacher",
    response_model=ShareToTeacherResponse,
    status_code=200,
)
def share_to_teacher(
    classroom_id: uuid.UUID,
    body: ShareToTeacherRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Share a workspace node with the classroom's teacher.

    The caller must be a student in this classroom.
    The node must be owned by the caller (enforced by the workspace share ACL check).

    On success the teacher immediately sees the node in their workspace
    Shared section with viewer access; changes made by the student are
    reflected in real-time.
    """
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_student_member(classroom, current_user.username, db)

    # Resolve teacher UUID from main DB
    from core.db.deps import get_db as get_main_db
    teacher_uuid: str | None = None
    for main_db in get_main_db():
        teacher = main_db.execute(
            select(User).where(User.username == classroom.owner)
        ).scalar_one_or_none()
        if teacher:
            teacher_uuid = str(teacher.id)
        break

    if not teacher_uuid:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not resolve teacher account.",
        )

    # student_uuid is available directly from current_user (main DB object)
    student_uuid = str(current_user.id)

    # Look up the student's subfolder in teacher's classroom/ workspace.
    # This is set when the student joins/is added to the classroom.
    student_folder_id: str | None = db.execute(
        select(ClassroomMember.workspace_folder_id).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.username == current_user.username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()

    ok = workspace_sync.sync_share_node_with_teacher(
        student_uuid=student_uuid,
        node_id=body.node_id,
        teacher_uuid=teacher_uuid,
        student_folder_id=student_folder_id,
    )
    if not ok:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Workspace share failed. Please try again.",
        )

    return ShareToTeacherResponse(
        ok=True,
        message="Shared successfully. Your teacher can now view this in their workspace.",
    )
