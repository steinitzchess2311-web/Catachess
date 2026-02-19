"""
catchat API router
==================
Aggregates all catchat sub-routers.
Mounted at /api/catchat in backend/main.py.

Full endpoint list:
  GET  /api/catchat/conversations
  POST /api/catchat/conversations
  GET  /api/catchat/conversations/{id}/messages
  POST /api/catchat/conversations/{id}/messages
  GET  /api/catchat/broadcasts
  POST /api/catchat/broadcasts
"""
from fastapi import APIRouter

from modules.catchat.api.conversations import router as conv_router
from modules.catchat.api.messages import router as msg_router
from modules.catchat.api.broadcasts import router as bcast_router

router = APIRouter()

router.include_router(conv_router)
router.include_router(msg_router)
router.include_router(bcast_router)
