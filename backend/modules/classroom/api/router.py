"""
Classroom API router
====================
Aggregates all classroom sub-routers.
Mounted at /api/classroom in backend/main.py.

Endpoints summary:

Classrooms:
  POST   /api/classroom/classrooms
  GET    /api/classroom/classrooms
  GET    /api/classroom/classrooms/{id}
  PATCH  /api/classroom/classrooms/{id}
  DELETE /api/classroom/classrooms/{id}
  POST   /api/classroom/classrooms/{id}/archive
  POST   /api/classroom/classrooms/{id}/unarchive
  GET    /api/classroom/classrooms/{id}/invite
  POST   /api/classroom/classrooms/{id}/invite/reset
  PATCH  /api/classroom/classrooms/{id}/invite
  POST   /api/classroom/classrooms/join
  GET    /api/classroom/classrooms/{id}/chat
  POST   /api/classroom/classrooms/{id}/broadcast

Members:
  GET    /api/classroom/classrooms/{id}/members
  POST   /api/classroom/classrooms/{id}/members
  DELETE /api/classroom/classrooms/{id}/members/{username}
  PATCH  /api/classroom/classrooms/{id}/members/{username}/role
  POST   /api/classroom/classrooms/{id}/members/leave

Assignments:
  POST   /api/classroom/classrooms/{id}/assignments
  GET    /api/classroom/classrooms/{id}/assignments
  GET    /api/classroom/classrooms/{id}/assignments/{aid}
  PATCH  /api/classroom/classrooms/{id}/assignments/{aid}
  DELETE /api/classroom/classrooms/{id}/assignments/{aid}
  GET    /api/classroom/classrooms/{id}/assignments/{aid}/stats

Submissions:
  POST   /api/classroom/classrooms/{id}/assignments/{aid}/submissions
  GET    /api/classroom/classrooms/{id}/assignments/{aid}/submissions
  GET    /api/classroom/classrooms/{id}/assignments/{aid}/submissions/me
  GET    /api/classroom/classrooms/{id}/assignments/{aid}/submissions/{username}
  GET    /api/classroom/classrooms/my/todo
"""
from fastapi import APIRouter

from modules.classroom.api.endpoints.classrooms import router as classrooms_router
from modules.classroom.api.endpoints.members import router as members_router
from modules.classroom.api.endpoints.assignments import router as assignments_router
from modules.classroom.api.endpoints.submissions import router as submissions_router

router = APIRouter()

router.include_router(classrooms_router)
router.include_router(members_router)
router.include_router(assignments_router)
router.include_router(submissions_router)
