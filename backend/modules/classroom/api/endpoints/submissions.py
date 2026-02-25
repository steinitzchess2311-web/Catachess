"""
Submission endpoints
====================
POST   /classrooms/{id}/assignments/{aid}/submissions        Start or submit (student)
GET    /classrooms/{id}/assignments/{aid}/submissions        All submissions (teacher+)
GET    /classrooms/{id}/assignments/{aid}/submissions/me     My submissions (student)
GET    /classrooms/{id}/assignments/{aid}/submissions/{uname} One student's submissions (teacher+)
GET    /classrooms/my/todo                                   Student todo across all classrooms
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.db.models.assignment import Assignment
from modules.classroom.db.models.target import AssignmentTarget
from modules.classroom.db.models.submission import Submission
from modules.classroom.schemas.submission import SubmissionUpsert, SubmissionResponse, TodoItem
from modules.classroom.services.todo import get_my_todo
from models.user import User

router = APIRouter(tags=["classroom-submissions"])


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


def _get_assignment_or_404(db: Session, classroom_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment:
    a = db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.classroom_id == classroom_id,
            Assignment.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return a


def _is_assigned_to(db: Session, assignment_id: uuid.UUID, username: str) -> bool:
    row = db.execute(
        select(AssignmentTarget).where(
            AssignmentTarget.assignment_id == assignment_id,
            (AssignmentTarget.target_type == "all") |
            ((AssignmentTarget.target_type == "user") & (AssignmentTarget.username == username)),
        ).limit(1)
    ).scalar_one_or_none()
    return row is not None


def _to_response(s: Submission) -> SubmissionResponse:
    return SubmissionResponse(
        id=str(s.id), assignment_id=str(s.assignment_id),
        username=s.username, attempt=s.attempt, status=s.status,
        score=s.score, detail=s.detail,
        started_at=s.started_at, submitted_at=s.submitted_at,
    )


# ── Start / submit ────────────────────────────────────────────────────────────

@router.post(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/submissions",
    response_model=SubmissionResponse,
    status_code=201,
)
def upsert_submission(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: SubmissionUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    if role not in ("student",):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only students can submit assignments")

    assignment = _get_assignment_or_404(db, classroom_id, assignment_id)
    username = current_user.username

    if not _is_assigned_to(db, assignment_id, username):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="This assignment is not assigned to you")

    # Check max_attempts
    latest = db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.username == username,
        ).order_by(Submission.attempt.desc()).limit(1)
    ).scalar_one_or_none()

    if latest and latest.status == "in_progress" and body.status == "in_progress":
        # Already in progress — update detail and return existing
        if body.detail is not None:
            latest.detail = body.detail
            db.commit()
            db.refresh(latest)
        return _to_response(latest)

    if latest and latest.status == "in_progress" and body.status == "submitted":
        # Close the current attempt
        latest.status = "submitted"
        latest.score = body.score
        if body.detail is not None:
            latest.detail = body.detail
        latest.submitted_at = datetime.now(tz=timezone.utc)
        db.commit()
        db.refresh(latest)
        return _to_response(latest)

    # Starting a new attempt
    if assignment.max_attempts is not None:
        completed = db.execute(
            select(Submission).where(
                Submission.assignment_id == assignment_id,
                Submission.username == username,
                Submission.status == "submitted",
            )
        ).scalars().all()
        if len(completed) >= assignment.max_attempts:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Maximum attempts ({assignment.max_attempts}) reached",
            )

    next_attempt = (latest.attempt + 1) if latest else 1
    sub = Submission(
        assignment_id=assignment_id,
        username=username,
        attempt=next_attempt,
        status=body.status,
        score=body.score if body.status == "submitted" else None,
        detail=body.detail,
        submitted_at=datetime.now(tz=timezone.utc) if body.status == "submitted" else None,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return _to_response(sub)


# ── Teacher: all submissions for an assignment ────────────────────────────────

@router.get(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/submissions",
    response_model=list[SubmissionResponse],
)
def list_all_submissions(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    _get_assignment_or_404(db, classroom_id, assignment_id)

    subs = db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
        ).order_by(Submission.username, Submission.attempt)
    ).scalars().all()

    return [_to_response(s) for s in subs]


# ── Student: my submissions ───────────────────────────────────────────────────

@router.get(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/submissions/me",
    response_model=list[SubmissionResponse],
)
def list_my_submissions(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _my_role(classroom, current_user.username, db)
    _get_assignment_or_404(db, classroom_id, assignment_id)

    subs = db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.username == current_user.username,
        ).order_by(Submission.attempt)
    ).scalars().all()

    return [_to_response(s) for s in subs]


# ── Teacher: one student's submissions ───────────────────────────────────────

@router.get(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/submissions/{username}",
    response_model=list[SubmissionResponse],
)
def list_student_submissions(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    _get_assignment_or_404(db, classroom_id, assignment_id)

    subs = db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.username == username,
        ).order_by(Submission.attempt)
    ).scalars().all()

    return [_to_response(s) for s in subs]


# ── Student: cross-classroom todo ─────────────────────────────────────────────

@router.get("/classrooms/my/todo", response_model=list[TodoItem])
def my_todo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_my_todo(username=current_user.username, db=db)
