"""
Tagger Players Router - 棋手与上传 API
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from core.db.deps import get_db
from modules.tagger import TaggerService
from schemas.tagger import (
    PlayerCreate, PlayerResponse, PlayerListResponse,
    UploadResponse, UploadStatusResponse, UploadListResponse,
    StatsListResponse, StatsResponse, TagStatItem,
    FailedGamesResponse, FailedGameItem,
)

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> TaggerService:
    return TaggerService(db)


# === Player Endpoints ===

@router.post("/players", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(request: PlayerCreate, svc: TaggerService = Depends(get_service)):
    return svc.create_player(request.display_name, request.aliases)


@router.get("/players", response_model=PlayerListResponse)
async def list_players(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    svc: TaggerService = Depends(get_service),
):
    players, total = svc.list_players(offset, limit)
    return PlayerListResponse(players=players, total=total)


@router.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: uuid.UUID, svc: TaggerService = Depends(get_service)):
    player = svc.get_player(player_id)
    if not player:
        raise HTTPException(404, "Player not found")
    return player


# === Upload Endpoints ===

@router.post("/players/{player_id}/uploads", response_model=UploadResponse)
async def upload_pgn(
    player_id: uuid.UUID,
    file: UploadFile = File(...),
    svc: TaggerService = Depends(get_service),
):
    if not svc.get_player(player_id):
        raise HTTPException(404, "Player not found")
    content = await file.read()
    upload_user_id = uuid.uuid4()  # TODO: 从 auth 获取
    upload = svc.create_upload(player_id, content, file.filename or "upload.pgn", upload_user_id)
    return UploadResponse(**svc.get_upload_status(upload.id))


@router.get("/players/{player_id}/uploads", response_model=UploadListResponse)
async def list_uploads(player_id: uuid.UUID, svc: TaggerService = Depends(get_service)):
    if not svc.get_player(player_id):
        raise HTTPException(404, "Player not found")
    uploads = svc.list_uploads(player_id)
    items = [svc.get_upload_status(u.id) for u in uploads]
    return UploadListResponse(uploads=[UploadResponse(**i) for i in items if i], total=len(items))


@router.get("/players/{player_id}/uploads/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(player_id: uuid.UUID, upload_id: uuid.UUID, svc: TaggerService = Depends(get_service)):
    info = svc.get_upload_status(upload_id)
    if not info:
        raise HTTPException(404, "Upload not found")
    return UploadStatusResponse(
        upload_id=info["id"], status=info["status"], processed_positions=info["processed_positions"],
        failed_games_count=info["failed_games_count"], last_updated=info["last_updated"],
    )


@router.get("/players/{player_id}/uploads/{upload_id}/failed", response_model=FailedGamesResponse)
async def get_failed_games(player_id: uuid.UUID, upload_id: uuid.UUID, svc: TaggerService = Depends(get_service)):
    failed = svc.get_failed_games(upload_id)
    items = [
        FailedGameItem(
            game_index=f.game_index, headers=f.headers, player_color=f.player_color, move_count=f.move_count,
            error_code=f.error_code, error_message=f.error_message, retry_count=f.retry_count, last_attempt_at=f.last_attempt_at,
        )
        for f in failed
    ]
    return FailedGamesResponse(upload_id=upload_id, failed_games=items, total=len(items))


# === Stats Endpoints ===

@router.get("/players/{player_id}/stats", response_model=StatsListResponse)
async def get_stats(player_id: uuid.UUID, svc: TaggerService = Depends(get_service)):
    if not svc.get_player(player_id):
        raise HTTPException(404, "Player not found")
    result = {}
    for scope in ["white", "black", "total"]:
        stats = svc.get_stats(player_id, scope)
        if stats:
            stat = stats[0]
            items = [
                TagStatItem(
                    tag_name=s.tag_name, tag_count=s.tag_count, total_positions=s.total_positions,
                    percentage=(s.tag_count / s.total_positions * 100) if s.total_positions else 0,
                )
                for s in stats
            ]
            result[scope] = StatsResponse(
                player_id=player_id, scope=scope, stats=items,
                engine_version=stat.engine_version, depth=stat.depth, multipv=stat.multipv, updated_at=stat.updated_at,
            )
    return StatsListResponse(**result)
