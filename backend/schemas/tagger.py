"""
Tagger API Schemas

请求/响应模型（来自 Stage 05）
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# === Player Schemas ===

class PlayerCreate(BaseModel):
    """创建棋手请求"""
    display_name: str = Field(..., min_length=1, max_length=200)
    aliases: list[str] = Field(default_factory=list)


class PlayerResponse(BaseModel):
    """棋手响应"""
    id: uuid.UUID
    display_name: str
    normalized_name: str
    aliases: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlayerListResponse(BaseModel):
    """棋手列表响应"""
    players: list[PlayerResponse]
    total: int


# === Upload Schemas ===

class UploadResponse(BaseModel):
    """上传响应（最小集，来自 Stage 05）"""
    id: uuid.UUID
    status: str
    processed_positions: int = 0
    failed_games_count: int = 0
    last_updated: datetime
    needs_confirmation: bool = False
    match_candidates: list[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UploadStatusResponse(BaseModel):
    """上传状态响应"""
    upload_id: uuid.UUID
    status: str
    processed_positions: int
    failed_games_count: int
    last_updated: datetime


class UploadListResponse(BaseModel):
    """上传列表响应"""
    uploads: list[UploadResponse]
    total: int


# === Stats Schemas ===

class TagStatItem(BaseModel):
    """单个标签统计"""
    tag_name: str
    tag_count: int
    total_positions: int
    percentage: float


class StatsResponse(BaseModel):
    """统计响应"""
    player_id: uuid.UUID
    scope: str  # white/black/total
    stats: list[TagStatItem]
    engine_version: str
    depth: int
    multipv: int
    updated_at: datetime


class StatsListResponse(BaseModel):
    """统计列表响应（白/黑/总）"""
    white: Optional[StatsResponse] = None
    black: Optional[StatsResponse] = None
    total: Optional[StatsResponse] = None


# === Failed Games Schemas ===

class FailedGameItem(BaseModel):
    """失败记录项"""
    game_index: int
    headers: Optional[dict]
    player_color: Optional[str]
    move_count: int
    error_code: str
    error_message: Optional[str]
    retry_count: int
    last_attempt_at: Optional[datetime]


class FailedGamesResponse(BaseModel):
    """失败记录响应"""
    upload_id: uuid.UUID
    failed_games: list[FailedGameItem]
    total: int


# === Export Schemas ===

class ExportParams(BaseModel):
    """导出参数（来自 Stage 05）"""
    upload_ids: Optional[str] = None  # 逗号分隔
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
