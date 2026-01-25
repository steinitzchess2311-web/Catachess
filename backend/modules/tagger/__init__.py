"""
Tagger Module - Pipeline 与存储调度

职责（来自 Stage 02）：
- backend/modules/tagger：pipeline 与存储调度
- 核心逻辑在此模块内
"""
from modules.tagger.errors import TaggerErrorCode, UploadStatus
from modules.tagger.storage import TaggerStorage, TaggerStorageConfig, TaggerKeyBuilder
from modules.tagger.service import TaggerService, normalize_name

__all__ = [
    "TaggerErrorCode",
    "UploadStatus",
    "TaggerStorage",
    "TaggerStorageConfig",
    "TaggerKeyBuilder",
    "TaggerService",
    "normalize_name",
]
