"""
Classroom API router
====================
Aggregates all classroom sub-routers.
Mounted at /api/classroom in backend/main.py.

Endpoints summary:

Classrooms (classrooms.py — CRUD + archive):
  POST   /api/classroom/classrooms
  GET    /api/classroom/classrooms
  GET    /api/classroom/classrooms/{id}
  PATCH  /api/classroom/classrooms/{id}
  DELETE /api/classroom/classrooms/{id}
  POST   /api/classroom/classrooms/{id}/archive
  POST   /api/classroom/classrooms/{id}/unarchive

Invites (invites.py — invite code + join):
  GET    /api/classroom/classrooms/{id}/invite
  POST   /api/classroom/classrooms/{id}/invite/reset
  PATCH  /api/classroom/classrooms/{id}/invite
  POST   /api/classroom/classrooms/join

Broadcasts (broadcasts.py — chat link + announcements):
  GET    /api/classroom/classrooms/{id}/chat
  POST   /api/classroom/classrooms/{id}/broadcast
  GET    /api/classroom/classrooms/{id}/broadcasts
  DELETE /api/classroom/classrooms/{id}/broadcasts/{mid}

Contact (contact.py — student→teacher chat):
  POST   /api/classroom/classrooms/{id}/contact-teacher

Members:
  GET    /api/classroom/classrooms/{id}/members
  POST   /api/classroom/classrooms/{id}/members
  DELETE /api/classroom/classrooms/{id}/members/{username}
  PATCH  /api/classroom/classrooms/{id}/members/{username}/role
  PATCH  /api/classroom/classrooms/{id}/members/{username}/folder
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

Activity:
  GET    /api/classroom/classrooms/{id}/activity

Materials:
  POST   /api/classroom/classrooms/{id}/assignments/{aid}/open-material
  GET    /api/classroom/classrooms/{id}/assignments/{aid}/forks

Workspace Shares:
  POST   /api/classroom/classrooms/{id}/share-to-teacher
"""
from fastapi import APIRouter

from modules.classroom.api.endpoints.classrooms import router as classrooms_router
from modules.classroom.api.endpoints.invites import router as invites_router
from modules.classroom.api.endpoints.broadcasts import router as broadcasts_router
from modules.classroom.api.endpoints.contact import router as contact_router
from modules.classroom.api.endpoints.members import router as members_router
from modules.classroom.api.endpoints.assignments import router as assignments_router
from modules.classroom.api.endpoints.submissions import router as submissions_router
from modules.classroom.api.endpoints.activity import router as activity_router
from modules.classroom.api.endpoints.shares import router as shares_router
from modules.classroom.api.endpoints.materials import router as materials_router

router = APIRouter()

router.include_router(classrooms_router)
router.include_router(invites_router)
router.include_router(broadcasts_router)
router.include_router(contact_router)
router.include_router(members_router)
router.include_router(assignments_router)
router.include_router(submissions_router)
router.include_router(activity_router)
router.include_router(shares_router)
router.include_router(materials_router)
