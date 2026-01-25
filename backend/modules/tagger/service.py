"""
Tagger Service - Pipeline 与存储调度

职责（来自 Stage 02/05）：
- 接收上传 → 写 R2 → 创建 upload 记录
- 触发解析 pipeline
- 写入统计与失败记录
- 返回进度与状态
"""
import uuid
import unicodedata
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from models.tagger import PlayerProfile, PgnUpload, PgnGame, FailedGame, TagStat
from modules.tagger.errors import UploadStatus
from modules.tagger.storage import TaggerStorage


def normalize_name(name: str) -> str:
    """规范化棋手名称"""
    normalized = unicodedata.normalize("NFKC", name.lower().strip())
    return "".join(c for c in normalized if c.isalnum() or c.isspace()).strip()


class TaggerService:
    """Tagger 主服务（在 modules/tagger 内）"""

    def __init__(self, db: Session, storage: Optional[TaggerStorage] = None):
        self.db = db
        self._storage = storage or TaggerStorage()

    # === Player Operations ===

    def create_player(self, display_name: str, aliases: list[str] = None) -> PlayerProfile:
        player = PlayerProfile(
            display_name=display_name,
            normalized_name=normalize_name(display_name),
            aliases=aliases or [],
        )
        self.db.add(player)
        self.db.commit()
        self.db.refresh(player)
        return player

    def get_player(self, player_id: uuid.UUID) -> Optional[PlayerProfile]:
        return self.db.get(PlayerProfile, player_id)

    def list_players(self, offset: int = 0, limit: int = 50) -> tuple[list[PlayerProfile], int]:
        total = self.db.scalar(select(func.count(PlayerProfile.id)))
        players = self.db.scalars(
            select(PlayerProfile).order_by(PlayerProfile.created_at.desc()).offset(offset).limit(limit)
        ).all()
        return list(players), total or 0

    # === Upload Operations ===

    def create_upload(
        self,
        player_id: uuid.UUID,
        pgn_content: bytes,
        original_filename: str,
        upload_user_id: uuid.UUID,
    ) -> PgnUpload:
        """创建上传记录，写 R2，触发 pipeline"""
        upload_id = uuid.uuid4()
        checksum = TaggerStorage.compute_checksum(pgn_content)

        r2_key_raw, _ = self._storage.upload_pgn(
            player_id, upload_id, pgn_content, original_filename, upload_user_id
        )

        upload = PgnUpload(
            id=upload_id,
            player_id=player_id,
            r2_key_raw=r2_key_raw,
            checksum=checksum,
            status=UploadStatus.PENDING.value,
        )
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)

        # 触发 pipeline（异步，Stage 06 实现）
        self._trigger_pipeline(upload)
        return upload

    def _trigger_pipeline(self, upload: PgnUpload) -> None:
        """触发解析 pipeline（Stage 06 实现具体逻辑）"""
        upload.status = UploadStatus.PROCESSING.value
        self.db.commit()
        # TODO: Stage 06 - 调用 pipeline 解析 PGN

    def get_upload(self, upload_id: uuid.UUID) -> Optional[PgnUpload]:
        return self.db.get(PgnUpload, upload_id)

    def list_uploads(self, player_id: uuid.UUID) -> list[PgnUpload]:
        """获取棋手的所有上传"""
        return list(self.db.scalars(
            select(PgnUpload).where(PgnUpload.player_id == player_id).order_by(PgnUpload.created_at.desc())
        ).all())

    def get_upload_status(self, upload_id: uuid.UUID) -> Optional[dict]:
        """获取上传状态（最小集字段）"""
        upload = self.get_upload(upload_id)
        if not upload:
            return None

        processed = self.db.scalar(
            select(func.sum(PgnGame.move_count)).where(PgnGame.upload_id == upload_id)
        ) or 0
        failed_count = self.db.scalar(
            select(func.count(FailedGame.id)).where(FailedGame.upload_id == upload_id)
        ) or 0

        return {
            "id": upload.id,
            "status": upload.status,
            "processed_positions": processed,
            "failed_games_count": failed_count,
            "last_updated": upload.updated_at,
            "needs_confirmation": upload.status == UploadStatus.NEEDS_CONFIRMATION.value,
            "match_candidates": (upload.checkpoint_state or {}).get("candidates", []),
        }

    # === Failed Games ===

    def get_failed_games(self, upload_id: uuid.UUID) -> list[FailedGame]:
        return list(self.db.scalars(
            select(FailedGame).where(FailedGame.upload_id == upload_id).order_by(FailedGame.game_index)
        ).all())

    # === Stats ===

    def get_stats(self, player_id: uuid.UUID, scope: str = None) -> list[TagStat]:
        query = select(TagStat).where(TagStat.player_id == player_id)
        if scope:
            query = query.where(TagStat.scope == scope)
        return list(self.db.scalars(query).all())

    def get_stats_filtered(
        self,
        player_id: uuid.UUID,
        upload_ids: list[uuid.UUID] = None,
        from_date: datetime = None,
        to_date: datetime = None,
    ) -> list[TagStat]:
        """获取统计（支持范围过滤）"""
        # 基础查询
        query = select(TagStat).where(TagStat.player_id == player_id)

        # TODO: upload_ids 过滤需要关联 games 表，Stage 06 实现
        # 时间过滤
        if from_date:
            query = query.where(TagStat.updated_at >= from_date)
        if to_date:
            query = query.where(TagStat.updated_at <= to_date)

        return list(self.db.scalars(query).all())
