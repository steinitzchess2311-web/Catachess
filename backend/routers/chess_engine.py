"""
Chess Engine Router

Exposes Analysis (Cloud Eval) to frontend.
Stage 11: Switched to Lichess Cloud Eval API.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.chess_engine.client import EngineClient
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
    source: str = "cloud-eval"


# Initialize engine client
# Note: We replaced the complex get_engine() factory with direct EngineClient usage
engine = EngineClient()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_position(request: AnalyzeRequest):
    """
    Analyze a chess position using Lichess Cloud Eval.

    Returns:
        AnalyzeResponse with principal variations
    """
    try:
        logger.info(f"Analyzing position: depth={request.depth}, multipv={request.multipv}")

        result = engine.analyze(
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
    return {
        "status": "healthy",
        "service": "lichess-cloud-eval",
    }