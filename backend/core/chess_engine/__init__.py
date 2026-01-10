"""Chess engine package - multi-spot orchestration."""
from core.config import settings
from core.chess_engine.client import EngineClient
from core.chess_engine.orchestrator.orchestrator import EngineOrchestrator
from core.chess_engine.config.spots import load_spots
from core.log.log_chess_engine import logger


def get_engine():
    """
    Factory function for engine client.
    Returns appropriate implementation based on feature flag.

    Returns:
        EngineClient (legacy) or EngineOrchestrator (multi-spot)
    """
    if settings.ENABLE_MULTI_SPOT:
        logger.info("Multi-spot engine enabled, initializing EngineOrchestrator")

        # Load spot configurations
        spot_configs = load_spots()

        if not spot_configs:
            logger.warning(
                "Multi-spot enabled but no spot configs found, "
                "falling back to legacy single-spot client"
            )
            return EngineClient(
                base_url=settings.ENGINE_URL,
                timeout=settings.ENGINE_TIMEOUT
            )

        # Create orchestrator with configured spots
        orchestrator = EngineOrchestrator(
            spot_configs=spot_configs,
            timeout=settings.SPOT_REQUEST_TIMEOUT,
            max_retries=settings.SPOT_MAX_RETRIES
        )
        logger.info(
            f"EngineOrchestrator initialized with {len(spot_configs)} spots, "
            f"timeout={settings.SPOT_REQUEST_TIMEOUT}s, max_retries={settings.SPOT_MAX_RETRIES}"
        )
        return orchestrator

    else:
        logger.info("Using legacy single-spot EngineClient")
        return EngineClient(
            base_url=settings.ENGINE_URL,
            timeout=settings.ENGINE_TIMEOUT
        )


# Public API
__all__ = ["get_engine", "EngineClient", "EngineOrchestrator"]
