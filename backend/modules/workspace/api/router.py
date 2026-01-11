"""
Main API router.
"""

from fastapi import APIRouter

from workspace.api.endpoints import nodes, shares, studies, discussions

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(nodes.router)
api_router.include_router(shares.router)
api_router.include_router(studies.router)
api_router.include_router(discussions.router)
