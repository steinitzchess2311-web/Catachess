"""Chess engine package - single-spot client."""
from core.config import settings
from core.chess_engine.client import EngineClient
from core.log.log_chess_engine import logger


def get_engine():
    """
    Factory function for engine client.

    Returns:
        EngineClient
    """
    if settings.ENABLE_MULTI_SPOT:
        logger.warning("Multi-spot engine is disabled in Stage 11, using single-spot client.")

    logger.info("Using single-spot EngineClient")
    return EngineClient(timeout=settings.ENGINE_TIMEOUT)


# Public API
__all__ = ["get_engine", "EngineClient"]
