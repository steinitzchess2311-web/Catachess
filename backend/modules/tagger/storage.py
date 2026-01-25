"""
Tagger Storage - Pipeline 存储调度

职责（来自 Stage 02）：
- R2 存储调度
- 元数据管理
"""
import json
import uuid
import hashlib
from datetime import datetime
from typing import TypedDict, Optional

from storage.core.client import StorageClient
from storage.core.config import StorageConfig


class TaggerMeta(TypedDict):
    """元数据结构（来自 Stage 03）"""
    checksum: str
    original_filename: str
    upload_user_id: str
    uploaded_at: str
    parser_version: str


class TaggerKeyBuilder:
    """R2 Key 生成器（来自 Stage 03）"""
    PREFIX = "players"

    @classmethod
    def raw_pgn(cls, player_id: uuid.UUID, upload_id: uuid.UUID) -> str:
        return f"{cls.PREFIX}/{player_id}/{upload_id}/raw.pgn"

    @classmethod
    def meta_json(cls, player_id: uuid.UUID, upload_id: uuid.UUID) -> str:
        return f"{cls.PREFIX}/{player_id}/{upload_id}/meta.json"


class TaggerStorageConfig:
    """Tagger 专用存储配置（来自 Stage 03）"""
    BUCKET_NAME = "catachess-pgn"
    PARSER_VERSION = "1.0.0"

    @classmethod
    def get_config(cls) -> StorageConfig:
        """获取配置，强制使用 tagger bucket"""
        config = StorageConfig.from_env()
        # 覆盖 bucket 为 tagger 专用
        config.bucket = cls.BUCKET_NAME
        return config


class TaggerStorage:
    """Tagger 存储操作"""

    def __init__(self, client: Optional[StorageClient] = None):
        if client is None:
            config = TaggerStorageConfig.get_config()
            client = StorageClient(config)
        self._client = client
        self._keys = TaggerKeyBuilder

    def upload_pgn(
        self,
        player_id: uuid.UUID,
        upload_id: uuid.UUID,
        pgn_content: bytes,
        original_filename: str,
        upload_user_id: uuid.UUID,
    ) -> tuple[str, str]:
        """上传 PGN 及元数据到 R2"""
        raw_key = self._keys.raw_pgn(player_id, upload_id)
        meta_key = self._keys.meta_json(player_id, upload_id)

        checksum = hashlib.sha256(pgn_content).hexdigest()
        meta: TaggerMeta = {
            "checksum": checksum,
            "original_filename": original_filename,
            "upload_user_id": str(upload_user_id),
            "uploaded_at": datetime.utcnow().isoformat(),
            "parser_version": TaggerStorageConfig.PARSER_VERSION,
        }

        self._client.put_object(raw_key, pgn_content, "application/x-chess-pgn")
        self._client.put_object(meta_key, json.dumps(meta).encode(), "application/json")
        return raw_key, meta_key

    def get_pgn(self, player_id: uuid.UUID, upload_id: uuid.UUID) -> bytes:
        """获取 PGN 内容"""
        return self._client.get_object(self._keys.raw_pgn(player_id, upload_id))

    def get_meta(self, player_id: uuid.UUID, upload_id: uuid.UUID) -> TaggerMeta:
        """获取元数据"""
        content = self._client.get_object(self._keys.meta_json(player_id, upload_id))
        return json.loads(content.decode())

    @staticmethod
    def compute_checksum(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
