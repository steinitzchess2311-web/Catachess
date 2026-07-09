"""
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

MongoDB Engine Cache

Global cache for chess engine analysis results.
"""

import time
from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from core.config import settings
from core.log.log_chess_engine import logger


class MongoEngineCache:
    """MongoDB-based engine analysis cache"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.collection: Optional[AsyncIOMotorCollection] = None
        self.initialized = False

        # Cache configuration
        self.db_name = getattr(settings, 'MONGODB_DATABASE', 'catachess')
        self.collection_name = getattr(settings, 'MONGODB_CACHE_COLLECTION', 'engine_cache')

    async def init(self):
        """Initialize MongoDB connection and create indexes"""
        if self.initialized:
            return

        mongo_url = getattr(settings, 'MONGO_URL', None)
        if not mongo_url:
            logger.warning("[MONGODB CACHE] MONGO_URL not configured, cache disabled")
            return

        try:
            logger.info(f"[MONGODB CACHE] Connecting to MongoDB...")
            self.client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,              # Maximum connections in pool (increased from default 100)
                minPoolSize=10,              # Minimum connections to maintain
                maxIdleTimeMS=45000,         # Close idle connections after 45 seconds
                connectTimeoutMS=10000,      # Connection timeout: 10 seconds
                socketTimeoutMS=20000,       # Socket timeout: 20 seconds
                waitQueueTimeoutMS=5000,     # Wait queue timeout: 5 seconds
            )

            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"[MONGODB CACHE] Connected successfully")

            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]

            # Create indexes
            await self._create_indexes()

            self.initialized = True
            logger.info(f"[MONGODB CACHE] Initialization complete")

        except Exception as e:
            logger.error(f"[MONGODB CACHE] Initialization failed: {e}")
            self.client = None
            self.db = None
            self.collection = None

    async def _create_indexes(self):
        """Create necessary indexes"""
        if self.collection is None:
            return

        try:
            indexes = [
                # Unique index on cache_key for fast lookup
                IndexModel([("cache_key", ASCENDING)], unique=True, name="cache_key_unique"),

                # Compound index for FEN-based queries
                IndexModel([
                    ("fen", ASCENDING),
                    ("depth", ASCENDING),
                    ("multipv", ASCENDING)
                ], name="fen_params"),

                # Timestamp index for time-based queries (NO TTL - permanent storage)
                IndexModel([("timestamp", ASCENDING)], name="timestamp_idx"),

                # Hot positions index for statistics
                IndexModel([
                    ("hit_count", DESCENDING),
                    ("timestamp", DESCENDING)
                ], name="hot_positions"),
            ]

            await self.collection.create_indexes(indexes)
            logger.info(f"[MONGODB CACHE] Indexes created successfully")

        except Exception as e:
            logger.warning(f"[MONGODB CACHE] Index creation warning: {e}")

    def _generate_cache_key(
        self,
        fen: str,
        depth: int,
        multipv: int,
        engine_mode: str | None = None,
    ) -> str:
        """Generate unique cache key scoped by engine mode."""
        mode = engine_mode or "auto"
        return f"engine:{mode}|fen:{fen}|depth:{depth}|multipv:{multipv}"

    async def get(self, fen: str, depth: int, multipv: int, engine_mode: str | None = None) -> Optional[dict]:
        """
        Get cached analysis result

        Returns:
            dict with 'lines', 'source', 'cache_key', 'timestamp' if found, None otherwise
        """
        if not self.initialized or self.collection is None:
            return None

        cache_key = self._generate_cache_key(fen, depth, multipv, engine_mode)
        query_start = time.time()

        try:
            result = await self.collection.find_one({"cache_key": cache_key})
            query_duration = time.time() - query_start

            if result:
                logger.info(
                    f"[MONGODB CACHE] ✓ HIT in {query_duration*1000:.1f}ms | "
                    f"key={cache_key[:60]}... | hits={result.get('hit_count', 0)}"
                )
                return {
                    "cache_key": cache_key,
                    "lines": result.get("lines", []),
                    "source": result.get("source"),
                    "engine_mode": result.get("engine_mode", engine_mode or "auto"),
                    "timestamp": result.get("timestamp"),
                    "hit_count": result.get("hit_count", 0),
                }
            else:
                logger.info(
                    f"[MONGODB CACHE] ✗ MISS in {query_duration*1000:.1f}ms | "
                    f"key={cache_key[:60]}..."
                )
                return None

        except Exception as e:
            query_duration = time.time() - query_start
            logger.error(
                f"[MONGODB CACHE] Query error in {query_duration*1000:.1f}ms: {e}"
            )
            return None

    async def set(
        self,
        fen: str,
        depth: int,
        multipv: int,
        lines: list[dict],
        source: str,
        engine_mode: str | None = None
    ) -> bool:
        """
        Store analysis result in cache

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.initialized or self.collection is None:
            return False

        cache_key = self._generate_cache_key(fen, depth, multipv, engine_mode)
        store_start = time.time()

        try:
            now = datetime.now(timezone.utc)

            # Use upsert to avoid duplicate key errors
            await self.collection.update_one(
                {"cache_key": cache_key},
                {
                    "$set": {
                        "cache_key": cache_key,
                        "fen": fen,
                        "depth": depth,
                        "multipv": multipv,
                        "engine_mode": engine_mode or "auto",
                        "lines": lines,
                        "source": source,
                        "timestamp": now,
                        "hit_count": 0,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    }
                },
                upsert=True
            )

            store_duration = time.time() - store_start
            logger.info(
                f"[MONGODB CACHE] ✓ STORED in {store_duration*1000:.1f}ms | "
                f"key={cache_key[:60]}... | lines={len(lines)}"
            )
            return True

        except Exception as e:
            store_duration = time.time() - store_start
            logger.error(
                f"[MONGODB CACHE] Store error in {store_duration*1000:.1f}ms: {e}"
            )
            return False

    async def increment_hit_count(self, cache_key: str):
        """Increment hit count for statistics"""
        if not self.initialized or self.collection is None:
            return

        try:
            await self.collection.update_one(
                {"cache_key": cache_key},
                {
                    "$inc": {"hit_count": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
        except Exception as e:
            logger.warning(f"[MONGODB CACHE] Hit count increment failed: {e}")

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.initialized or self.collection is None:
            return {
                "enabled": False,
                "total_entries": 0,
                "estimated_size_mb": 0,
            }

        try:
            total = await self.collection.count_documents({})

            # Get collection stats
            stats = await self.db.command("collStats", self.collection_name)
            size_bytes = stats.get("size", 0)
            size_mb = size_bytes / (1024 * 1024)

            return {
                "enabled": True,
                "total_entries": total,
                "estimated_size_mb": round(size_mb, 2),
                "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                "avg_obj_size_bytes": stats.get("avgObjSize", 0),
            }

        except Exception as e:
            logger.error(f"[MONGODB CACHE] Stats error: {e}")
            return {
                "enabled": True,
                "error": str(e),
            }

    async def get_hot_positions(self, limit: int = 10) -> list[dict]:
        """Get most frequently accessed positions"""
        if not self.initialized or self.collection is None:
            return []

        try:
            cursor = self.collection.find(
                {"hit_count": {"$gt": 0}},
                {"cache_key": 1, "fen": 1, "hit_count": 1, "timestamp": 1}
            ).sort("hit_count", DESCENDING).limit(limit)

            results = await cursor.to_list(length=limit)
            return [
                {
                    "fen": r.get("fen", "")[:50] + "...",
                    "hit_count": r.get("hit_count", 0),
                    "timestamp": r.get("timestamp"),
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"[MONGODB CACHE] Hot positions error: {e}")
            return []

    async def clear(self) -> int:
        """Clear all cache entries (for testing/maintenance only!)"""
        if not self.initialized or self.collection is None:
            return 0

        try:
            result = await self.collection.delete_many({})
            deleted = result.deleted_count
            logger.warning(f"[MONGODB CACHE] ⚠️ Cleared ALL {deleted} entries")
            return deleted

        except Exception as e:
            logger.error(f"[MONGODB CACHE] Clear error: {e}")
            return 0

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("[MONGODB CACHE] Connection closed")
            self.initialized = False


# Singleton instance
_cache_instance: Optional[MongoEngineCache] = None


async def get_mongo_cache() -> MongoEngineCache:
    """Get or create the global MongoDB cache instance"""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = MongoEngineCache()
        await _cache_instance.init()

    return _cache_instance
