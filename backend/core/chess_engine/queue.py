"""
Engine Request Queue

Implements a global queue for engine analysis requests to prevent
a single user from overwhelming the backend.

Architecture:
    HTTP Request
      ↓
    Backend (rate limit)
      ↓
    Engine Queue (排队 + 去重)
      ↓
    Engine Workers (有限个: 3 workers)
      ↓
    sf.catachess / Lichess Cloud Eval
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional
from core.log.log_chess_engine import logger


@dataclass
class EngineRequest:
    """A queued engine analysis request"""
    fen: str
    depth: int
    multipv: int
    engine: str
    future: asyncio.Future  # To return result to caller
    enqueued_at: float


@dataclass
class QueueStats:
    """Statistics for monitoring queue health"""
    queue_size: int
    active_workers: int
    total_requests: int
    total_completed: int
    total_failed: int
    avg_wait_time_ms: float
    avg_processing_time_ms: float


class EngineQueue:
    """
    Global engine request queue with worker pool.

    Features:
    - Request deduplication (same request waits for existing result)
    - Limited concurrency (max_workers = 3)
    - FIFO queue processing
    - Statistics tracking
    """

    def __init__(self, max_workers: int = 3):
        """
        Initialize the engine queue.

        Args:
            max_workers: Maximum concurrent engine calls (default: 3)
        """
        self._queue: asyncio.Queue = asyncio.Queue()
        self._max_workers = max_workers
        self._active_workers = 0
        self._workers: list[asyncio.Task] = []

        # Request deduplication: cache_key -> Future
        # Multiple callers waiting for the same analysis share the same Future
        self._pending_requests: Dict[str, asyncio.Future] = {}

        # Statistics
        self._stats = {
            "total_requests": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_deduplicated": 0,
            "wait_times": [],
            "processing_times": [],
        }

        self._running = False

    def start(self):
        """Start the worker pool"""
        if self._running:
            return

        self._running = True
        logger.info(f"[ENGINE QUEUE] Starting with {self._max_workers} workers")

        # Create worker tasks
        for i in range(self._max_workers):
            worker = asyncio.create_task(self._worker(worker_id=i))
            self._workers.append(worker)

    async def stop(self):
        """Stop the worker pool and drain queue"""
        logger.info("[ENGINE QUEUE] Stopping workers...")
        self._running = False

        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        logger.info("[ENGINE QUEUE] Stopped")

    async def enqueue(
        self,
        fen: str,
        depth: int,
        multipv: int,
        engine: str,
        engine_callable
    ) -> dict:
        """
        Enqueue an engine analysis request.

        If an identical request is already pending, this will wait for
        that request's result instead of creating a duplicate.

        Args:
            fen: Position FEN
            depth: Analysis depth
            multipv: Number of variations
            engine: Engine mode ('sf', 'cloud', 'auto')
            engine_callable: The actual engine.analyze() function

        Returns:
            Engine analysis result

        Raises:
            Exception: If engine call fails
        """
        # Create cache key for deduplication
        cache_key = self._make_cache_key(fen, depth, multipv, engine)

        # Check if identical request already pending
        if cache_key in self._pending_requests:
            self._stats["total_deduplicated"] += 1
            logger.info(f"[ENGINE QUEUE] Deduplicating request | Key: {cache_key}")

            # Wait for existing request to complete
            existing_future = self._pending_requests[cache_key]
            try:
                result = await existing_future
                return result
            except Exception as e:
                # If the existing request failed, re-raise the error
                raise e

        # Create new request
        future = asyncio.Future()
        self._pending_requests[cache_key] = future

        request = EngineRequest(
            fen=fen,
            depth=depth,
            multipv=multipv,
            engine=engine,
            future=future,
            enqueued_at=time.time(),
        )

        self._stats["total_requests"] += 1
        queue_size = self._queue.qsize()

        logger.info(
            f"[ENGINE QUEUE] Enqueued request | "
            f"Queue size: {queue_size} | Active workers: {self._active_workers}"
        )

        # Add to queue
        await self._queue.put((request, engine_callable))

        # Wait for result
        try:
            result = await future
            return result
        finally:
            # Clean up pending request entry
            self._pending_requests.pop(cache_key, None)

    async def _worker(self, worker_id: int):
        """
        Worker coroutine that processes queued requests.

        Args:
            worker_id: Worker identifier for logging
        """
        logger.info(f"[ENGINE QUEUE] Worker {worker_id} started")

        while self._running:
            try:
                # Wait for request (with timeout to allow graceful shutdown)
                try:
                    request, engine_callable = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process request
                self._active_workers += 1
                processing_start = time.time()
                wait_time = processing_start - request.enqueued_at

                cache_key = self._make_cache_key(
                    request.fen, request.depth, request.multipv, request.engine
                )

                logger.info(
                    f"[ENGINE QUEUE] Worker {worker_id} processing | "
                    f"Wait time: {wait_time*1000:.0f}ms | "
                    f"Queue size: {self._queue.qsize()}"
                )

                try:
                    # Delegate the synchronous engine call to a thread-pool
                    # worker so it never blocks the event loop.
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        None,  # default ThreadPoolExecutor
                        lambda: engine_callable(
                            fen=request.fen,
                            depth=request.depth,
                            multipv=request.multipv,
                            engine=request.engine,
                        ),
                    )

                    processing_time = time.time() - processing_start

                    # Record statistics
                    self._stats["wait_times"].append(wait_time * 1000)
                    self._stats["processing_times"].append(processing_time * 1000)
                    self._stats["total_completed"] += 1

                    # Keep only last 100 timing samples
                    if len(self._stats["wait_times"]) > 100:
                        self._stats["wait_times"] = self._stats["wait_times"][-100:]
                    if len(self._stats["processing_times"]) > 100:
                        self._stats["processing_times"] = self._stats["processing_times"][-100:]

                    logger.info(
                        f"[ENGINE QUEUE] Worker {worker_id} completed | "
                        f"Processing time: {processing_time*1000:.0f}ms | "
                        f"Total wait: {wait_time*1000:.0f}ms"
                    )

                    # Return result to caller
                    if not request.future.done():
                        request.future.set_result(result)

                except Exception as e:
                    self._stats["total_failed"] += 1
                    logger.error(
                        f"[ENGINE QUEUE] Worker {worker_id} failed | Error: {e}"
                    )

                    # Propagate error to caller
                    if not request.future.done():
                        request.future.set_exception(e)

                finally:
                    self._active_workers -= 1
                    self._queue.task_done()

            except Exception as e:
                logger.error(f"[ENGINE QUEUE] Worker {worker_id} error: {e}")

        logger.info(f"[ENGINE QUEUE] Worker {worker_id} stopped")

    def get_stats(self) -> QueueStats:
        """Get current queue statistics"""
        wait_times = self._stats["wait_times"]
        processing_times = self._stats["processing_times"]

        return QueueStats(
            queue_size=self._queue.qsize(),
            active_workers=self._active_workers,
            total_requests=self._stats["total_requests"],
            total_completed=self._stats["total_completed"],
            total_failed=self._stats["total_failed"],
            avg_wait_time_ms=sum(wait_times) / len(wait_times) if wait_times else 0,
            avg_processing_time_ms=sum(processing_times) / len(processing_times) if processing_times else 0,
        )

    @staticmethod
    def _make_cache_key(fen: str, depth: int, multipv: int, engine: str) -> str:
        """Create a cache key for request deduplication"""
        return f"fen:{fen}|depth:{depth}|multipv:{multipv}|engine:{engine}"


# Global queue instance
_global_queue: Optional[EngineQueue] = None


def get_engine_queue() -> EngineQueue:
    """Get or create the global engine queue"""
    global _global_queue
    if _global_queue is None:
        # Load max_workers from config
        try:
            from core.config import settings
            max_workers = settings.ENGINE_QUEUE_MAX_WORKERS
        except Exception:
            max_workers = 3  # Fallback default

        _global_queue = EngineQueue(max_workers=max_workers)
        _global_queue.start()
    return _global_queue


async def shutdown_engine_queue():
    """Shutdown the global engine queue (for cleanup)"""
    global _global_queue
    if _global_queue is not None:
        await _global_queue.stop()
        _global_queue = None
