"""
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Chess Engine Router

Exposes Analysis (Cloud Eval) to frontend.
Stage 11: Switched to Lichess Cloud Eval API.
Stage 12: Added MongoDB global cache.
Stage 13: Added engine request queue + rate limiting.
Stage 14: Added local Stockfish worker capability and AlphaZero worker status.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from core.chess_engine.client import EngineClient
from core.chess_engine.local_workers import get_engine_capabilities
from core.chess_engine.queue import get_engine_queue
from core.errors import ChessEngineError, ChessEngineTimeoutError
from core.log.log_chess_engine import logger
from core.cache import get_mongo_cache
from core.security.rate_limiter import rate_limit


router = APIRouter(
    prefix="/api/engine",
    tags=["chess-engine"],
)


class AnalyzeRequest(BaseModel):
    """Request to analyze a chess position"""
    fen: str
    depth: int = 15
    multipv: int = 3
    engine: str | None = None


class AnalyzeResponse(BaseModel):
    """Analysis result from engine"""
    lines: list[dict]
    source: str | None = None
    cache_metadata: dict | None = None  # MongoDB cache metadata for frontend logging


class CacheStoreRequest(BaseModel):
    fen: str
    depth: int
    multipv: int
    lines: list[dict]
    source: str
    engine_mode: str | None = None


# Initialize engine client
# Note: We replaced the complex get_engine() factory with direct EngineClient usage
engine = EngineClient()


def _get_rate_limit_dependency():
    """Create rate limit dependency with configured limit"""
    from core.config import settings
    limit = settings.ENGINE_RATE_LIMIT_PER_MINUTE
    return rate_limit(limit=limit, window_seconds=60)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(_get_rate_limit_dependency())]
)
async def analyze_position(request: AnalyzeRequest):
    """
    Analyze a chess position using MongoDB cache → Engine Queue → Engine.

    Flow:
    1. Check MongoDB global cache
    2. If hit: return cached result (fast path)
    3. If miss: enqueue to engine queue → process with limited concurrency → store in MongoDB → return

    Rate limit: 30 requests/minute/IP

    Returns:
        AnalyzeResponse with principal variations
    """
    import time
    start_time = time.time()

    try:
        logger.info("=" * 80)
        logger.info(f"[ENGINE ANALYZE] Request started")
        logger.info(f"[ENGINE ANALYZE] FEN: {request.fen}")
        logger.info(f"[ENGINE ANALYZE] Depth: {request.depth}, MultiPV: {request.multipv}, Engine: {request.engine or 'auto'}")

        # Step 1: Check MongoDB cache
        mongo_cache = await get_mongo_cache()
        engine_mode = request.engine or 'auto'

        mongo_start = time.time()
        cache_result = await mongo_cache.get(
            fen=request.fen,
            depth=request.depth,
            multipv=request.multipv,
            engine_mode=engine_mode
        )
        mongo_duration = time.time() - mongo_start

        if cache_result:
            # Cache hit - return immediately
            await mongo_cache.increment_hit_count(cache_result['cache_key'])

            total_duration = time.time() - start_time
            logger.info(f"[ENGINE ANALYZE] ✓ MongoDB cache HIT")
            logger.info(f"[ENGINE ANALYZE] Source: {cache_result['source']}_cached")
            logger.info(f"[ENGINE ANALYZE] Lines returned: {len(cache_result['lines'])}")
            logger.info(f"[ENGINE ANALYZE] Total duration: {total_duration:.3f}s (cache hit)")
            logger.info("=" * 80)

            return AnalyzeResponse(
                lines=cache_result['lines'],
                source=f"{cache_result['source']}_cached",
                cache_metadata={
                    "mongodb_hit": True,
                    "mongodb_query_ms": round(mongo_duration * 1000, 1),
                    "hit_count": cache_result.get('hit_count', 0),
                    "cached_at": str(cache_result.get('timestamp', '')),
                    "total_ms": round(total_duration * 1000, 1),
                }
            )

        # Step 2: Cache miss - enqueue to engine queue
        logger.info(f"[ENGINE ANALYZE] ✗ MongoDB cache MISS - enqueuing to engine queue")

        engine_queue = get_engine_queue()
        engine_start = time.time()

        # Enqueue request (will wait in queue if workers busy)
        result = await engine_queue.enqueue(
            fen=request.fen,
            depth=request.depth,
            multipv=request.multipv,
            engine=request.engine or 'auto',
            engine_callable=engine.analyze,
        )

        engine_duration = time.time() - engine_start

        # Convert to response format
        lines = [
            {
                "multipv": line.multipv,
                "score": line.score,
                "pv": line.pv,
            }
            for line in result.lines
        ]

        # Step 3: Store in MongoDB cache
        store_start = time.time()
        await mongo_cache.set(
            fen=request.fen,
            depth=request.depth,
            multipv=request.multipv,
            engine_mode=engine_mode,
            lines=lines,
            source=result.source
        )
        store_duration = time.time() - store_start

        total_duration = time.time() - start_time
        logger.info(f"[ENGINE ANALYZE] Analysis complete")
        logger.info(f"[ENGINE ANALYZE] Source: {result.source}")
        logger.info(f"[ENGINE ANALYZE] Lines returned: {len(lines)}")
        logger.info(f"[ENGINE ANALYZE] Engine call duration: {engine_duration:.3f}s")
        logger.info(f"[ENGINE ANALYZE] MongoDB store duration: {store_duration:.3f}s")
        logger.info(f"[ENGINE ANALYZE] Total duration: {total_duration:.3f}s")
        logger.info("=" * 80)

        return AnalyzeResponse(
            lines=lines,
            source=result.source,
            cache_metadata={
                "mongodb_hit": False,
                "mongodb_query_ms": round(mongo_duration * 1000, 1),
                "mongodb_store_ms": round(store_duration * 1000, 1),
                "engine_ms": round(engine_duration * 1000, 1),
                "total_ms": round(total_duration * 1000, 1),
            }
        )

    except ChessEngineTimeoutError as e:
        logger.error(f"Engine timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Engine request timed out after {e.timeout}s"
        )
    except ChessEngineError as e:
        logger.error(f"Engine error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Analysis unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze position: {str(e)}"
        )


@router.get("/health")
async def engine_health():
    """
    Check engine health.
    """
    capabilities = get_engine_capabilities()
    engine_queue = get_engine_queue()
    stats = engine_queue.get_stats()
    return {
        "status": "healthy",
        "service": "catachess-engine",
        "queue": {
            "queue_size": stats.queue_size,
            "active_workers": stats.active_workers,
            "max_workers": engine_queue.max_workers,
            "total_requests": stats.total_requests,
            "total_completed": stats.total_completed,
            "total_failed": stats.total_failed,
        },
        "engines": [
            {
                "key": capability.key,
                "label": capability.label,
                "available": capability.available,
                "status": capability.status,
                "detail": capability.detail,
                "concurrency_limit": capability.concurrency_limit,
                "active_workers": capability.active_workers,
                "binary": capability.binary,
            }
            for capability in capabilities
        ],
    }


@router.get("/cache/stats")
async def cache_stats():
    """
    Get MongoDB cache statistics.
    """
    try:
        mongo_cache = await get_mongo_cache()
        stats = await mongo_cache.get_stats()
        hot_positions = await mongo_cache.get_hot_positions(limit=10)

        return {
            "cache": stats,
            "hot_positions": hot_positions,
            "note": "Data is stored permanently (no auto-expiration)",
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {
            "cache": {"enabled": False, "error": str(e)},
            "hot_positions": [],
        }


@router.get("/cache/lookup")
async def cache_lookup(fen: str, depth: int = 15, multipv: int = 3, engine_mode: str = "auto"):
    """
    Lookup MongoDB cache entry without triggering engine.
    """
    try:
        mongo_cache = await get_mongo_cache()
        cache_result = await mongo_cache.get(
            fen=fen,
            depth=depth,
            multipv=multipv,
            engine_mode=engine_mode,
        )
        if not cache_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cache miss"
            )

        ts = cache_result.get("timestamp")
        timestamp_ms = int(ts.timestamp() * 1000) if ts else None

        return {
            "lines": cache_result.get("lines", []),
            "source": cache_result.get("source"),
            "engine_mode": cache_result.get("engine_mode"),
            "timestamp_ms": timestamp_ms,
            "hit_count": cache_result.get("hit_count", 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache lookup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache lookup failed: {str(e)}"
        )


@router.post("/cache/store")
async def cache_store(request: CacheStoreRequest):
    """
    Store analysis result in MongoDB cache (no engine call).
    """
    try:
        mongo_cache = await get_mongo_cache()
        await mongo_cache.set(
            fen=request.fen,
            depth=request.depth,
            multipv=request.multipv,
            engine_mode=request.engine_mode or "auto",
            lines=request.lines,
            source=request.source,
        )
        return {"ok": True}
    except Exception as e:
        logger.error(f"Cache store error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache store failed: {str(e)}"
        )


@router.get("/queue/stats")
async def queue_stats():
    """
    Get engine request queue statistics.

    Returns:
        queue_size: Number of requests waiting in queue
        active_workers: Number of workers currently processing
        total_requests: Total requests enqueued since startup
        total_completed: Total requests completed
        total_failed: Total requests failed
        avg_wait_time_ms: Average time requests wait in queue
        avg_processing_time_ms: Average time to process a request
    """
    try:
        engine_queue = get_engine_queue()
        stats = engine_queue.get_stats()

        return {
            "queue_size": stats.queue_size,
            "active_workers": stats.active_workers,
            "max_workers": engine_queue.max_workers,
            "total_requests": stats.total_requests,
            "total_completed": stats.total_completed,
            "total_failed": stats.total_failed,
            "avg_wait_time_ms": round(stats.avg_wait_time_ms, 1),
            "avg_processing_time_ms": round(stats.avg_processing_time_ms, 1),
        }
    except Exception as e:
        logger.error(f"Queue stats error: {e}")
        return {
            "queue_size": 0,
            "active_workers": 0,
            "error": str(e),
        }
