"""
Material fork endpoints
=======================
POST  /classrooms/{id}/assignments/{aid}/open-material   Student opens material → fork
GET   /classrooms/{id}/assignments/{aid}/forks            Teacher views all forks
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.db.models.assignment import Assignment
from modules.classroom.db.models.material_fork import MaterialFork
from modules.classroom.services import workspace_sync
from models.user import User

router = APIRouter(tags=["classroom-materials"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class OpenMaterialResponse(BaseModel):
    fork_study_id: str
    fork_chapter_id: str
    is_new: bool


class ForkItem(BaseModel):
    student_username: str
    fork_study_id: str
    fork_chapter_id: str
    created_at: str


# ── Helpers ──────────────────────────────────────────────────────────────────

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


# ── Open Material ────────────────────────────────────────────────────────────

@router.post(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/open-material",
    response_model=OpenMaterialResponse,
)
def open_material(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Student opens a material assignment. If no fork exists yet, one is created
    by deep-copying the teacher's chapter into the student's workspace folder.
    """
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    if role not in ("student",):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only students can open material")

    assignment = db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.classroom_id == classroom_id,
            Assignment.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if not assignment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if assignment.category != "material" or assignment.source_type != "study":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Assignment is not a study material")

    # Check for existing fork
    existing = db.execute(
        select(MaterialFork).where(
            MaterialFork.assignment_id == assignment_id,
            MaterialFork.student_username == current_user.username,
        )
    ).scalar_one_or_none()

    if existing:
        return OpenMaterialResponse(
            fork_study_id=existing.fork_study_id,
            fork_chapter_id=existing.fork_chapter_id,
            is_new=False,
        )

    # Parse source_ref = "{study_id}/{chapter_id}"
    source_ref = assignment.source_ref or ""
    parts = source_ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid source_ref format")
    source_study_id, source_chapter_id = parts

    # Resolve UUIDs
    teacher_uuid = _resolve_user_uuid(classroom.owner)
    if not teacher_uuid:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not resolve teacher account")

    student_uuid = str(current_user.id)

    # Get student's workspace folder
    student_folder_id: str | None = db.execute(
        select(ClassroomMember.workspace_folder_id).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.username == current_user.username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()

    # Fork
    result = workspace_sync.sync_fork_material(
        teacher_uuid=teacher_uuid,
        student_uuid=student_uuid,
        student_folder_id=student_folder_id,
        source_study_id=source_study_id,
        source_chapter_id=source_chapter_id,
        assignment_title=assignment.title,
    )
    if not result:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to create material fork. Please try again.",
        )

    fork_study_id, fork_chapter_id = result

    # Save to DB
    fork = MaterialFork(
        assignment_id=assignment_id,
        student_username=current_user.username,
        fork_study_id=fork_study_id,
        fork_chapter_id=fork_chapter_id,
    )
    db.add(fork)
    db.commit()

    return OpenMaterialResponse(
        fork_study_id=fork_study_id,
        fork_chapter_id=fork_chapter_id,
        is_new=True,
    )


# ── List Forks (teacher view) ───────────────────────────────────────────────

@router.get(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/forks",
    response_model=list[ForkItem],
)
def list_forks(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all student forks for a material assignment (teacher/owner only)."""
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    if role not in ("owner", "teacher"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Teacher role required")

    forks = db.execute(
        select(MaterialFork).where(
            MaterialFork.assignment_id == assignment_id,
        ).order_by(MaterialFork.created_at.desc())
    ).scalars().all()

    return [
        ForkItem(
            student_username=f.student_username,
            fork_study_id=f.fork_study_id,
            fork_chapter_id=f.fork_chapter_id,
            created_at=f.created_at.isoformat() if f.created_at else "",
        )
        for f in forks
    ]
