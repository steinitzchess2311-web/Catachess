"""
Main API router.
"""

from fastapi import APIRouter

from modules.workspace.api.endpoints import discussions, nodes, public, search, shares, studies, notifications, versions, presence, users
from modules.workspace.api.websocket import presence_ws

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(public.router)
api_router.include_router(nodes.router)
api_router.include_router(shares.router)
api_router.include_router(studies.router)
api_router.include_router(discussions.router)
api_router.include_router(search.router)
api_router.include_router(notifications.router)
api_router.include_router(versions.router)
api_router.include_router(presence.router)
api_router.include_router(presence_ws.router)
api_router.include_router(users.router)
