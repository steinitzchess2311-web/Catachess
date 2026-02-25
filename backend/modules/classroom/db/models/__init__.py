"""
Import all classroom ORM models so SQLAlchemy's Base.metadata is fully
populated before create_all() is called on startup.
"""
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.db.models.assignment import Assignment
from modules.classroom.db.models.target import AssignmentTarget
from modules.classroom.db.models.submission import Submission

__all__ = [
    "Classroom",
    "ClassroomMember",
    "Assignment",
    "AssignmentTarget",
    "Submission",
]
