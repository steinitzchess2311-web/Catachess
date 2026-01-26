"""
Tagger Service - Pipeline 与存储调度

职责（来自 Stage 02/05）：
- 接收上传 → 写 R2 → 创建 upload 记录
- 触发解析 pipeline
- 写入统计与失败记录
- 返回进度与状态
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from models.tagger import PlayerProfile, PgnUpload, PgnGame, FailedGame, TagStat
from modules.tagger.delete import delete_player_records
from modules.tagger.errors import UploadStatus
from modules.tagger.storage import TaggerStorage
from modules.tagger.logs import append_upload_log
from modules.tagger.pipeline.pipeline import TaggerPipeline
from modules.tagger.utils import normalize_name


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

    def delete_player(self, player_id: uuid.UUID) -> bool:
        return delete_player_records(self.db, player_id)

    def recompute_player(self, player_id: uuid.UUID) -> list[PgnUpload]:
        player = self.get_player(player_id)
        if not player:
            return []
        self.db.query(FailedGame).filter(FailedGame.player_id == player_id).delete(synchronize_session=False)
        self.db.query(PgnGame).filter(PgnGame.player_id == player_id).delete(synchronize_session=False)
        self.db.query(TagStat).filter(TagStat.player_id == player_id).delete(synchronize_session=False)
        uploads = self.list_uploads(player_id)
        for upload in uploads:
            upload.status = UploadStatus.PENDING.value
            upload.checkpoint_state = None
            upload.updated_at = datetime.utcnow()
        self.db.commit()
        for upload in uploads:
            self._trigger_pipeline(upload)
        return uploads

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
        append_upload_log(self.db, upload, "Upload received.")
        append_upload_log(self.db, upload, "PGN stored in R2.")
        append_upload_log(self.db, upload, "Upload record created.")

        # 触发 pipeline（异步，Stage 06 实现）
        self._trigger_pipeline(upload)
        return upload

    def _trigger_pipeline(self, upload: PgnUpload) -> None:
        """触发解析 pipeline（Stage 06 实现具体逻辑）"""
        upload.status = UploadStatus.PROCESSING.value
        self.db.commit()
        append_upload_log(self.db, upload, "Analysis queued.")
        pipeline = TaggerPipeline(self.db, self._storage)
        player = self.get_player(upload.player_id)
        if not player:
            upload.status = UploadStatus.FAILED.value
            self.db.commit()
            append_upload_log(self.db, upload, "Upload failed: player not found.", level="error")
            return
        pipeline.process_upload(upload, player)

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

        checkpoint_state = upload.checkpoint_state or {}
        return {
            "id": upload.id,
            "status": upload.status,
            "processed_positions": processed,
            "failed_games_count": failed_count,
            "total_games": checkpoint_state.get("total_games", 0),
            "processed_games": checkpoint_state.get("processed_games", 0),
            "duplicate_games": checkpoint_state.get("duplicate_games", 0),
            "last_game_index": checkpoint_state.get("last_game_index"),
            "last_game_status": checkpoint_state.get("last_game_status"),
            "last_game_move_count": checkpoint_state.get("last_game_move_count"),
            "last_game_color": checkpoint_state.get("last_game_color"),
            "last_updated": upload.updated_at,
            "needs_confirmation": upload.status == UploadStatus.NEEDS_CONFIRMATION.value,
            "match_candidates": checkpoint_state.get("candidates", []),
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
