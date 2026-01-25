"""
Tagger Router Package

API 列表（来自 Stage 02）：
- POST /api/tagger/players
- GET /api/tagger/players
- GET /api/tagger/players/:id
- POST /api/tagger/players/:id/uploads
- GET /api/tagger/players/:id/uploads
- GET /api/tagger/players/:id/uploads/:upload_id/status
- GET /api/tagger/players/:id/uploads/:upload_id/failed
- GET /api/tagger/players/:id/stats
- GET /api/tagger/players/:id/exports
"""
from fastapi import APIRouter

from routers.tagger.players import router as players_router
from routers.tagger.exports import router as exports_router

router = APIRouter(prefix="/api/tagger", tags=["tagger"])
router.include_router(players_router)
router.include_router(exports_router)
