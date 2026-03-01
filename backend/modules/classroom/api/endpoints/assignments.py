"""
Assignment endpoints
====================
POST   /classrooms/{id}/assignments              Publish assignment (teacher+)
GET    /classrooms/{id}/assignments              List assignments (any member)
GET    /classrooms/{id}/assignments/{aid}        Assignment detail (any member)
PATCH  /classrooms/{id}/assignments/{aid}        Edit (creator or owner)
DELETE /classrooms/{id}/assignments/{aid}        Soft-delete (creator or owner)
GET    /classrooms/{id}/assignments/{aid}/stats  Submission stats (teacher+)
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.db.models.assignment import Assignment
from modules.classroom.db.models.target import AssignmentTarget
from modules.classroom.db.models.submission import Submission
from modules.classroom.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentListItem, AssignmentStats, AssignmentStatsPerStudent,
    TargetAll, TargetUsers,
)
from models.user import User

router = APIRouter(tags=["classroom-assignments"])


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


def _load_targets(db: Session, assignment_id: uuid.UUID) -> TargetAll | TargetUsers:
    rows = db.execute(
        select(AssignmentTarget).where(AssignmentTarget.assignment_id == assignment_id)
    ).scalars().all()
    for r in rows:
        if r.target_type == "all":
            return TargetAll(type="all")
    usernames = [r.username for r in rows if r.username]
    return TargetUsers(type="users", usernames=usernames)


def _is_visible_to(db: Session, assignment_id: uuid.UUID, username: str) -> bool:
    row = db.execute(
        select(AssignmentTarget).where(
            AssignmentTarget.assignment_id == assignment_id,
            (AssignmentTarget.target_type == "all") |
            ((AssignmentTarget.target_type == "user") & (AssignmentTarget.username == username)),
        ).limit(1)
    ).scalar_one_or_none()
    return row is not None


def _batch_visible_ids(
    db: Session, assignment_ids: list[uuid.UUID], username: str
) -> set[uuid.UUID]:
    """Return the set of assignment IDs visible to `username` — single query."""
    if not assignment_ids:
        return set()
    rows = db.execute(
        select(AssignmentTarget.assignment_id).where(
            AssignmentTarget.assignment_id.in_(assignment_ids),
            (AssignmentTarget.target_type == "all") |
            ((AssignmentTarget.target_type == "user") & (AssignmentTarget.username == username)),
        ).distinct()
    ).scalars().all()
    return set(rows)


def _batch_latest_submissions(
    db: Session, assignment_ids: list[uuid.UUID], username: str
) -> dict[uuid.UUID, Submission]:
    """Return the latest submission per assignment for `username` — single query."""
    if not assignment_ids:
        return {}
    rows = db.execute(
        select(Submission).where(
            Submission.assignment_id.in_(assignment_ids),
            Submission.username == username,
        )
    ).scalars().all()
    latest: dict[uuid.UUID, Submission] = {}
    for s in rows:
        if s.assignment_id not in latest or s.attempt > latest[s.assignment_id].attempt:
            latest[s.assignment_id] = s
    return latest


def _batch_submission_counts(
    db: Session, assignment_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """Return submitted-count per assignment for teacher view — single query."""
    if not assignment_ids:
        return {}
    rows = db.execute(
        select(Submission.assignment_id, func.count().label("cnt"))
        .where(
            Submission.assignment_id.in_(assignment_ids),
            Submission.status == "submitted",
        )
        .group_by(Submission.assignment_id)
    ).all()
    return {row.assignment_id: row.cnt for row in rows}


def _to_response(a: Assignment, targets, db: Session) -> AssignmentResponse:
    return AssignmentResponse(
        id=str(a.id), classroom_id=str(a.classroom_id),
        created_by=a.created_by, category=a.category, type=a.type,
        title=a.title, description=a.description,
        source_type=a.source_type, source_ref=a.source_ref,
        due_date=a.due_date, time_limit=a.time_limit, max_attempts=a.max_attempts,
        created_at=a.created_at, targets=targets,
    )


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/classrooms/{classroom_id}/assignments", response_model=AssignmentResponse, status_code=201)
def create_assignment(
    classroom_id: uuid.UUID,
    body: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)

    assignment = Assignment(
        classroom_id=classroom_id,
        created_by=current_user.username,
        category=body.category,
        type=body.type,
        title=body.title.strip(),
        description=body.description,
        source_type=body.source_type,
        source_ref=body.source_ref,
        due_date=body.due_date,
        time_limit=body.time_limit,
        max_attempts=body.max_attempts,
    )
    db.add(assignment)
    db.flush()

    # Write targets
    if isinstance(body.targets, TargetAll):
        db.add(AssignmentTarget(assignment_id=assignment.id, target_type="all", username=None))
    else:
        for uname in set(body.targets.usernames):
            db.add(AssignmentTarget(assignment_id=assignment.id, target_type="user", username=uname))

    db.commit()
    db.refresh(assignment)
    return _to_response(assignment, body.targets, db)


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/assignments", response_model=list[AssignmentListItem])
def list_assignments(
    classroom_id: uuid.UUID,
    category: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    username = current_user.username

    query = select(Assignment).where(
        Assignment.classroom_id == classroom_id,
        Assignment.deleted_at.is_(None),
    )
    if category:
        query = query.where(Assignment.category == category)

    assignments = db.execute(query.order_by(Assignment.created_at.desc())).scalars().all()

    assignment_ids = [a.id for a in assignments]

    if role == "student":
        # Batch: which assignments are visible to this student?
        visible_ids = _batch_visible_ids(db, assignment_ids, username)
        # Batch: latest submission per assignment
        latest_subs = _batch_latest_submissions(db, assignment_ids, username)
    else:
        # Batch: submitted count per assignment
        sub_counts = _batch_submission_counts(db, assignment_ids)

    result = []
    for a in assignments:
        if role == "student":
            if a.id not in visible_ids:
                continue
            sub = latest_subs.get(a.id)
            my_submission = (
                {"status": sub.status, "score": sub.score, "attempt": sub.attempt}
                if sub else None
            )
            result.append(AssignmentListItem(
                id=str(a.id), title=a.title, category=a.category,
                type=a.type, due_date=a.due_date, created_at=a.created_at,
                my_submission=my_submission,
            ))
        else:
            result.append(AssignmentListItem(
                id=str(a.id), title=a.title, category=a.category,
                type=a.type, due_date=a.due_date, created_at=a.created_at,
                submission_count=sub_counts.get(a.id, 0),
            ))

    return result


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/assignments/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    assignment = _get_assignment_or_404(db, classroom_id, assignment_id)

    if role == "student" and not _is_visible_to(db, assignment_id, current_user.username):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Assignment not assigned to you")

    return _to_response(assignment, _load_targets(db, assignment_id), db)


# ── Edit ──────────────────────────────────────────────────────────────────────

@router.patch("/classrooms/{classroom_id}/assignments/{assignment_id}", response_model=AssignmentResponse)
def edit_assignment(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: AssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    assignment = _get_assignment_or_404(db, classroom_id, assignment_id)

    # Only creator or owner may edit
    if assignment.created_by != current_user.username and classroom.owner != current_user.username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only the creator or owner may edit this assignment")

    if body.title is not None:
        assignment.title = body.title.strip()
    if body.description is not None:
        assignment.description = body.description
    if body.due_date is not None:
        assignment.due_date = body.due_date
    if body.time_limit is not None:
        assignment.time_limit = body.time_limit
    if body.max_attempts is not None:
        assignment.max_attempts = body.max_attempts

    db.commit()
    db.refresh(assignment)
    return _to_response(assignment, _load_targets(db, assignment_id), db)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/classrooms/{classroom_id}/assignments/{assignment_id}", status_code=204)
def delete_assignment(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    assignment = _get_assignment_or_404(db, classroom_id, assignment_id)

    if assignment.created_by != current_user.username and classroom.owner != current_user.username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only the creator or owner may delete this assignment")

    assignment.deleted_at = datetime.utcnow()
    db.commit()


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/classrooms/{classroom_id}/assignments/{assignment_id}/stats", response_model=AssignmentStats)
def assignment_stats(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    classroom = _get_classroom_or_404(db, classroom_id)
    _require_teacher(classroom, current_user.username, db)
    assignment = _get_assignment_or_404(db, classroom_id, assignment_id)

    # All students in classroom (members with role=student + consider targets)
    all_students = db.execute(
        select(ClassroomMember.username).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.role == "student",
            ClassroomMember.removed_at.is_(None),
        )
    ).scalars().all()

    targets = _load_targets(db, assignment_id)
    if isinstance(targets, TargetUsers):
        target_students = set(targets.usernames) & set(all_students)
    else:
        target_students = set(all_students)

    # Latest submission per student
    submissions = db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.username.in_(list(target_students)),
        )
    ).scalars().all()

    latest: dict[str, Submission] = {}
    for s in submissions:
        if s.username not in latest or s.attempt > latest[s.username].attempt:
            latest[s.username] = s

    now = datetime.now(tz=timezone.utc)
    submitted_count = 0
    in_progress_count = 0
    not_started_count = 0
    overdue_count = 0
    scores = []
    per_student = []

    for uname in target_students:
        sub = latest.get(uname)
        if sub is None:
            my_status = "not_started"
        else:
            my_status = sub.status

        is_overdue = (
            assignment.due_date
            and my_status != "submitted"
            and now > assignment.due_date.replace(tzinfo=timezone.utc)
        ) if assignment.due_date else False

        if my_status == "submitted":
            submitted_count += 1
            if sub.score is not None:
                scores.append(sub.score)
        elif my_status == "in_progress":
            in_progress_count += 1
        else:
            not_started_count += 1

        if is_overdue:
            overdue_count += 1

        per_student.append(AssignmentStatsPerStudent(
            username=uname,
            status=my_status,
            score=sub.score if sub else None,
            attempt=sub.attempt if sub else None,
            submitted_at=sub.submitted_at if sub else None,
        ))

    per_student.sort(key=lambda x: x.username)

    return AssignmentStats(
        assignment_id=str(assignment_id),
        total_targets=len(target_students),
        submitted=submitted_count,
        in_progress=in_progress_count,
        not_started=not_started_count,
        overdue=overdue_count,
        avg_score=sum(scores) / len(scores) if scores else None,
        score_distribution=sorted(scores),
        per_student=per_student,
    )
