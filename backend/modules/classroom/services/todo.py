"""
Todo Service
============
Computes a student's pending assignments across all their classrooms.

Urgency rules:
  'overdue'  — due_date has passed and student has not submitted
  'due_soon' — due_date is within 48 hours and student has not submitted
  'normal'   — not yet urgent (or no due_date)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.db.models.assignment import Assignment
from modules.classroom.db.models.target import AssignmentTarget
from modules.classroom.db.models.submission import Submission
from modules.classroom.schemas.submission import TodoItem

_DUE_SOON_WINDOW = timedelta(hours=48)


def _urgency(due_date: Optional[datetime], status: str) -> str:
    if status == "submitted":
        return "normal"
    if due_date is None:
        return "normal"
    now = datetime.now(tz=timezone.utc)
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)
    if now > due_date:
        return "overdue"
    if due_date - now <= _DUE_SOON_WINDOW:
        return "due_soon"
    return "normal"


def get_my_todo(username: str, db: Session) -> list[TodoItem]:
    """Return all pending assignments for a student, sorted by urgency then due_date."""

    # 1. Find all active classrooms the user belongs to
    memberships = db.execute(
        select(ClassroomMember.classroom_id).where(
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalars().all()

    if not memberships:
        return []

    classroom_ids = list(memberships)

    # 2. Load classroom names for display
    classrooms = db.execute(
        select(Classroom).where(
            Classroom.id.in_(classroom_ids),
            Classroom.deleted_at.is_(None),
            Classroom.archived_at.is_(None),
        )
    ).scalars().all()
    classroom_map = {str(c.id): c.name for c in classrooms}
    active_ids = list(classroom_map.keys())

    if not active_ids:
        return []

    # 3. Load assignments in those classrooms visible to this user
    assignments = db.execute(
        select(Assignment).where(
            Assignment.classroom_id.in_([uuid for uuid in classroom_ids
                                         if str(uuid) in active_ids]),
            Assignment.deleted_at.is_(None),
        )
    ).scalars().all()

    if not assignments:
        return []

    assignment_ids = [a.id for a in assignments]
    assignment_map = {a.id: a for a in assignments}

    # 4. Filter to assignments targeted at this user
    targets = db.execute(
        select(AssignmentTarget).where(
            AssignmentTarget.assignment_id.in_(assignment_ids),
        )
    ).scalars().all()

    visible_ids: set = set()
    for t in targets:
        if t.target_type == "all":
            visible_ids.add(t.assignment_id)
        elif t.target_type == "user" and t.username == username:
            visible_ids.add(t.assignment_id)

    if not visible_ids:
        return []

    # 5. Load existing submissions to determine status
    submissions = db.execute(
        select(Submission).where(
            Submission.assignment_id.in_(list(visible_ids)),
            Submission.username == username,
        )
    ).scalars().all()

    # Latest attempt per assignment
    latest: dict = {}
    for s in submissions:
        aid = s.assignment_id
        if aid not in latest or s.attempt > latest[aid].attempt:
            latest[aid] = s

    # 6. Build TodoItem list
    items: list[TodoItem] = []
    for aid in visible_ids:
        a = assignment_map[aid]
        sub = latest.get(aid)
        my_status = sub.status if sub else "not_started"
        urgency = _urgency(a.due_date, my_status)

        items.append(TodoItem(
            assignment_id=str(a.id),
            title=a.title,
            category=a.category,
            classroom_id=str(a.classroom_id),
            classroom_name=classroom_map.get(str(a.classroom_id), ""),
            due_date=a.due_date,
            urgency=urgency,
            my_status=my_status,
        ))

    # Sort: overdue first, then due_soon, then normal; within each group by due_date asc
    _order = {"overdue": 0, "due_soon": 1, "normal": 2}
    items.sort(key=lambda x: (
        _order[x.urgency],
        x.due_date or datetime.max.replace(tzinfo=timezone.utc),
    ))

    return items
