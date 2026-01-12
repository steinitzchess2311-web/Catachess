"""
Idempotency service for preventing duplicate operations.

Provides mechanisms to ensure that repeated requests with the same
idempotency key produce the same result without side effects.
"""

import hashlib
import json
from datetime import datetime, UTC, timedelta
from typing import Any, Optional
import logging

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.idempotency_cache import IdempotencyCache

logger = logging.getLogger(__name__)


class IdempotencyService:
    """
    Service for managing idempotent operations.

    Supports both explicit idempotency keys (from X-Idempotency-Key header)
    and automatic key generation based on request content.
    """

    DEFAULT_TTL_SECONDS = 86400  # 24 hours

    def __init__(self, session: AsyncSession):
        """
        Initialize idempotency service.

        Args:
            session: Database session
        """
        self.session = session

    async def check_idempotency_key(self, key: str) -> Optional[dict[str, Any]]:
        """
        Check if an idempotency key exists and return cached result.

        Args:
            key: Idempotency key

        Returns:
            Cached result if key exists and not expired, None otherwise
        """
        result = await self.session.execute(
            select(IdempotencyCache).where(
                IdempotencyCache.key == key,
                IdempotencyCache.expires_at > datetime.now(UTC)
            )
        )
        cache_entry = result.scalar_one_or_none()

        if cache_entry:
            logger.debug(f"Idempotency key hit: {key}")
            return cache_entry.result

        logger.debug(f"Idempotency key miss: {key}")
        return None

    async def cache_idempotency_result(
        self,
        key: str,
        result: dict[str, Any],
        ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> None:
        """
        Cache the result of an idempotent operation.

        Args:
            key: Idempotency key
            result: Result to cache
            ttl_seconds: Time-to-live in seconds (default: 24 hours)
        """
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)

        cache_entry = IdempotencyCache(
            key=key,
            result=result,
            expires_at=expires_at
        )

        # Use merge to handle the case where key already exists
        self.session.add(cache_entry)
        await self.session.flush()

        logger.debug(f"Cached idempotency result: {key}, expires at {expires_at}")

    async def generate_key_from_request(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Generate an idempotency key from request parameters.

        Useful for automatic idempotency without explicit key.

        Args:
            method: HTTP method (POST, PUT, etc.)
            path: Request path
            body: Request body (JSON)
            user_id: User ID (for user-specific idempotency)

        Returns:
            Generated idempotency key
        """
        # Create a stable representation of the request
        key_parts = [method, path]

        if user_id:
            key_parts.append(f"user:{user_id}")

        if body:
            # Sort keys for stable JSON serialization
            body_json = json.dumps(body, sort_keys=True)
            key_parts.append(body_json)

        # Hash the parts
        key_string = "|".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()

        return f"auto:{key_hash[:32]}"

    async def cleanup_expired(self) -> int:
        """
        Clean up expired idempotency cache entries.

        Returns:
            Number of entries deleted
        """
        result = await self.session.execute(
            delete(IdempotencyCache).where(
                IdempotencyCache.expires_at < datetime.now(UTC)
            )
        )

        count = result.rowcount
        if count > 0:
            logger.info(f"Cleaned up {count} expired idempotency cache entries")

        return count

    async def invalidate_key(self, key: str) -> bool:
        """
        Invalidate (delete) a specific idempotency key.

        Args:
            key: Idempotency key to invalidate

        Returns:
            True if key was deleted, False if not found
        """
        result = await self.session.execute(
            delete(IdempotencyCache).where(IdempotencyCache.key == key)
        )

        deleted = result.rowcount > 0
        if deleted:
            logger.debug(f"Invalidated idempotency key: {key}")

        return deleted


# Helper function for generating idempotency keys
def generate_idempotency_key(*parts: str) -> str:
    """
    Generate an idempotency key from multiple parts.

    Args:
        *parts: String parts to include in the key

    Returns:
        Generated idempotency key (hash of parts)

    Example:
        >>> generate_idempotency_key("user123", "study456", "create_chapter")
        'idem:abc123...'
    """
    key_string = "|".join(parts)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()
    return f"idem:{key_hash[:32]}"
