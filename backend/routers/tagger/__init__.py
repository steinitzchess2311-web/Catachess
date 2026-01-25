"""
Tagger Router Package

API 列表（来自 Stage 02）：
- POST /api/tagger/players
- GET /api/tagger/players
- GET /api/tagger/players/:id
- DELETE /api/tagger/players/:id
- POST /api/tagger/players/:id/recompute
- POST /api/tagger/players/:id/uploads
- GET /api/tagger/players/:id/uploads
- GET /api/tagger/players/:id/uploads/:upload_id/status
- GET /api/tagger/players/:id/uploads/:upload_id/failed
- GET /api/tagger/players/:id/stats
- GET /api/tagger/players/:id/exports
"""
import re
from fastapi import APIRouter, Request, Response
from core.config import settings

from routers.tagger.players import router as players_router
from routers.tagger.exports import router as exports_router

router = APIRouter(prefix="/api/tagger", tags=["tagger"])
router.include_router(players_router)
router.include_router(exports_router)


def _cors_headers_for_request(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if not origin:
        return {}
    allowed = origin in settings.cors_origins_list
    if not allowed and settings.CORS_ORIGIN_REGEX:
        try:
            allowed = re.match(settings.CORS_ORIGIN_REGEX, origin) is not None
        except re.error:
            allowed = False
    if not allowed:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Authorization,Content-Type",
        "Vary": "Origin",
    }


@router.options("/{path:path}")
async def tagger_cors_preflight(path: str, request: Request):
    return Response(status_code=204, headers=_cors_headers_for_request(request))


 # NOTE: APIRouter does not support middleware.
 # Tagger routes rely on the global CORSMiddleware in backend/main.py.
