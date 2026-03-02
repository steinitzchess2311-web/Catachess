"""
Classroom R2 storage client singleton.

Reuses the existing R2_* environment variables (same Cloudflare account,
same bucket as workspace). Data is isolated by key prefix: materials/{classroom_id}/...
"""
import logging
import os

from storage.core.client import StorageClient
from storage.core.config import StorageConfig

logger = logging.getLogger(__name__)

_client: StorageClient | None = None


def get_classroom_storage() -> StorageClient:
    """Return (or create) the singleton StorageClient for classroom materials."""
    global _client
    if _client is None:
        # Reuse existing R2 env vars — same account, same bucket.
        # Classroom data is isolated via key prefix (materials/...).
        config = StorageConfig(
            endpoint=os.environ["R2_ENDPOINT"],
            bucket=os.getenv("CLASSROOM_R2_BUCKET", os.environ.get("R2_BUCKET", "workspace")),
            access_key_id=os.environ["R2_ACCESS_KEY"],
            secret_access_key=os.environ["R2_SECRET_KEY"],
        )
        _client = StorageClient(config)
        logger.info("Classroom R2 storage client initialised: %r", _client)
    return _client
