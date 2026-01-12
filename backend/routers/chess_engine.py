"""
Chess Engine Router

Exposes Stockfish engine analysis to frontend.
Uses the multi-spot engine orchestrator with automatic failover.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.chess_engine import get_engine
from core.chess_engine.schemas import EngineResult
from core.errors import ChessEngineError, ChessEngineTimeoutError
from core.log.log_chess_engine import logger


router = APIRouter(
    prefix="/api/engine",
    tags=["chess-engine"],
)


class AnalyzeRequest(BaseModel):
    """Request to analyze a chess position"""
    fen: str
    depth: int = 15
    multipv: int = 3


class AnalyzeResponse(BaseModel):
    """Analysis result from engine"""
    lines: list[dict]


# Initialize engine client (automatically selects single-spot or multi-spot)
engine = get_engine()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_position(request: AnalyzeRequest):
    """
    Analyze a chess position using Stockfish engine

    The engine client automatically handles:
    - Multi-spot routing with failover
    - Priority-based spot selection
    - Timeout and retry logic

    Returns:
        AnalyzeResponse with multiple principal variations
    """
    try:
        logger.info(f"Analyzing position: depth={request.depth}, multipv={request.multipv}")

        result: EngineResult = engine.analyze(
            fen=request.fen,
            depth=request.depth,
            multipv=request.multipv,
        )

        # Convert to response format
        lines = [
            {
                "multipv": line.multipv,
                "score": line.score,
                "pv": line.pv,
            }
            for line in result.lines
        ]

        logger.info(f"Analysis complete: {len(lines)} lines")
        return AnalyzeResponse(lines=lines)

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
            detail=f"Chess engine unavailable: {str(e)}"
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
    Check engine health and get spot metrics

    Returns information about all configured engine spots
    """
    try:
        # Get spot metrics if using multi-spot orchestrator
        if hasattr(engine, 'get_spot_metrics'):
            metrics = engine.get_spot_metrics()
            spots_info = [
                {
                    "id": config.id,
                    "url": config.url,
                    "region": config.region,
                    "priority": config.priority,
                    "enabled": config.enabled,
                    "status": metrics.status.value,
                    "avg_latency_ms": metrics.avg_latency_ms,
                    "success_rate": metrics.success_rate,
                    "total_requests": metrics.total_requests,
                    "failure_count": metrics.failure_count,
                }
                for config, metrics in metrics
            ]
            return {
                "status": "healthy",
                "engine_type": "multi-spot",
                "spots": spots_info,
            }
        else:
            # Single-spot mode
            return {
                "status": "healthy",
                "engine_type": "single-spot",
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Engine health check failed: {str(e)}"
        )
