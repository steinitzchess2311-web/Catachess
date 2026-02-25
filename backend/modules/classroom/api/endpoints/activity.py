"""
Activity feed endpoint
======================
GET /classrooms/{id}/activity    Recent submission events across all assignments
                                 in a classroom (teacher view, newest first).
"""
import uuid

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.db.models.assignment import Assignment
from modules.classroom.db.models.submission import Submission
from modules.classroom.schemas.submission import ActivityItem
from models.user import User

router = APIRouter(tags=["classroom-activity"])


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


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/activity", response_model=list[ActivityItem])
def get_activity(
    classroom_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns recent submission activity for a classroom.
    Ordered by most recent event (submitted_at or started_at) descending.

    Teacher/owner only.
    """
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    if role not in ("owner", "teacher"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Teacher role required")

    # Load all non-deleted assignments in this classroom
    assignment_ids_q = db.execute(
        select(Assignment.id, Assignment.title, Assignment.category).where(
            Assignment.classroom_id == classroom_id,
            Assignment.deleted_at.is_(None),
        )
    ).all()

    if not assignment_ids_q:
        return []

    assignment_meta = {str(row.id): (row.title, row.category) for row in assignment_ids_q}
    ids = list(assignment_meta.keys())

    # Load submissions, most recent first
    # COALESCE(submitted_at, started_at) gives the most relevant timestamp
    from sqlalchemy import func, case
    subs = db.execute(
        select(Submission)
        .where(Submission.assignment_id.in_(ids))
        .order_by(
            func.coalesce(Submission.submitted_at, Submission.started_at).desc()
        )
        .limit(limit)
    ).scalars().all()

    result = []
    for s in subs:
        title, category = assignment_meta.get(str(s.assignment_id), ("", ""))
        result.append(ActivityItem(
            submission_id=str(s.id),
            student_username=s.username,
            assignment_id=str(s.assignment_id),
            assignment_title=title,
            assignment_category=category,
            attempt=s.attempt,
            status=s.status,
            score=s.score,
            submitted_at=s.submitted_at,
            started_at=s.started_at,
        ))

    return result
