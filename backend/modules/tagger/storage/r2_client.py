"""
Tagger Storage - Pipeline 存储调度

职责（来自 Stage 03）：
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
    BUCKET_NAME = "catachess-tagger"
    PARSER_VERSION = "1.0.0"
    ENV_PREFIX = "TAGGER_R2"

    @classmethod
    def get_config(cls) -> StorageConfig:
        """
        获取 tagger 专用存储配置。

        优先读取 TAGGER_R2_* 环境变量，若无则从通用 R2_* 读取并使用专用 bucket。
        """
        import os
        # 新增：支持 Railway 风格的 R2_TAGGER_* 变量
        r2_tagger_bucket = os.getenv("R2_TAGGER")
        r2_tagger_access = os.getenv("R2_TAGGER_ACCESS_KEY")
        r2_tagger_secret = os.getenv("R2_TAGGER_SECRET_KEY")
        if r2_tagger_bucket and r2_tagger_access and r2_tagger_secret:
            endpoint = (
                os.getenv("R2_TAGGER_ENDPOINT")
                or os.getenv("TAGGER_R2_ENDPOINT")
                or os.getenv("R2_ENDPOINT")
            )
            if endpoint:
                return StorageConfig(
                    endpoint=endpoint,
                    bucket=r2_tagger_bucket,
                    access_key_id=r2_tagger_access,
                    secret_access_key=r2_tagger_secret,
                    region=os.getenv("R2_TAGGER_REGION", "auto"),
                    account_id=os.getenv("R2_TAGGER_ACCOUNT_ID"),
                )

        # 优先使用 tagger 专用环境变量
        try:
            return StorageConfig.from_env(prefix=cls.ENV_PREFIX)
        except ValueError:
            pass

        # 回退：使用通用配置但创建新实例指定 tagger bucket
        base = StorageConfig.from_env()
        return StorageConfig(
            endpoint=base.endpoint,
            bucket=os.getenv("TAGGER_R2_BUCKET", cls.BUCKET_NAME),
            access_key_id=base.access_key_id,
            secret_access_key=base.secret_access_key,
            region=base.region,
            account_id=base.account_id,
        )


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

    def delete_key(self, key: str) -> None:
        """删除 R2 对象"""
        self._client.delete_object(key)

    @staticmethod
    def compute_checksum(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
