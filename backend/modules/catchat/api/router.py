"""
catchat API router
==================
Aggregates all catchat sub-routers.
Mounted at /api/catchat in backend/main.py.

Private chat endpoints:
  GET  /api/catchat/conversations
  POST /api/catchat/conversations
  GET  /api/catchat/conversations/{id}/messages
  POST /api/catchat/conversations/{id}/messages
  GET  /api/catchat/broadcasts
  POST /api/catchat/broadcasts
  GET  /api/catchat/notifications

Group chat endpoints:
  POST   /api/catchat/groups
  GET    /api/catchat/groups
  GET    /api/catchat/groups/{id}
  PATCH  /api/catchat/groups/{id}
  DELETE /api/catchat/groups/{id}
  POST   /api/catchat/groups/{id}/members
  DELETE /api/catchat/groups/{id}/members/{user_id}
  PATCH  /api/catchat/groups/{id}/members/{user_id}
  GET    /api/catchat/groups/{id}/messages
  POST   /api/catchat/groups/{id}/messages
"""
from fastapi import APIRouter

from modules.catchat.api.conversations import router as conv_router
from modules.catchat.api.messages import router as msg_router
from modules.catchat.api.broadcasts import router as bcast_router
from modules.catchat.api.notifications import router as notif_router
from modules.catchat.api.groups import router as groups_router
from modules.catchat.api.group_messages import router as group_messages_router

router = APIRouter()

# Private chat
router.include_router(conv_router)
router.include_router(msg_router)
router.include_router(bcast_router)
router.include_router(notif_router)

# Group chat
router.include_router(groups_router)
router.include_router(group_messages_router)
