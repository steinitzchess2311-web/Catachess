"""Engine orchestrator - routes requests and handles failover."""
from typing import List
from core.chess_engine.schemas import EngineResult
from core.chess_engine.fallback import analyze_legal_moves
from core.chess_engine.spot.models import SpotConfig
from core.chess_engine.orchestrator.pool import EngineSpotPool
from core.log.log_chess_engine import logger
from core.errors import ChessEngineError, ChessEngineTimeoutError
from core.config import settings


class EngineOrchestrator:
    """
    Orchestrates requests across multiple engine spots.
    Handles routing, retry, and failover.
    """

    # Optimized defaults for batch processing (100+ nodes in < 5s target)
    DEFAULT_TIMEOUT = 10  # Reduced from 30s for faster fail-over
    DEFAULT_MAX_RETRIES = 1  # Reduced from 2 for faster throughput

    def __init__(self, spot_configs: List[SpotConfig] = None, timeout: int = None, max_retries: int = None):
        """
        Initialize orchestrator.

        Args:
            spot_configs: List of spot configurations (optional)
            timeout: Request timeout in seconds (default: 10s)
            max_retries: Maximum number of retries (default: 1, total attempts = 2)
        """
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
        self.pool = EngineSpotPool(timeout=timeout)
        self.last_spot_id: str | None = None

        if spot_configs:
            self.pool.register_spots(spot_configs)

        logger.info(
            f"EngineOrchestrator initialized: "
            f"{self.pool.get_spot_count()} spots, timeout={timeout}s, max_retries={max_retries}"
        )

    def analyze(self, fen: str, depth: int = 15, multipv: int = 3) -> EngineResult:
        """
        Analyze a position using the best available spot with automatic failover.

        Args:
            fen: FEN string
            depth: Analysis depth
            multipv: Number of principal variations

        Returns:
            EngineResult with analysis

        Raises:
            ChessEngineError: If all spots fail or no spots available
        """
        # Get all usable spots in priority order
        usable_spots = self.pool.get_usable_spots()

        if not usable_spots:
            logger.error("No usable spots available")
            raise ChessEngineError("No engine spots available")

        # Try spots in order until one succeeds
        attempts = 0
        max_attempts = min(len(usable_spots), self.max_retries + 1)
        errors = []

        for spot in usable_spots[:max_attempts]:
            attempts += 1
            try:
                logger.info(
                    f"[Attempt {attempts}/{max_attempts}] Routing to spot: {spot.config.id}"
                )
                result = spot.analyze(fen, depth=depth, multipv=multipv)
                self.last_spot_id = spot.config.id
                logger.info(f"Request succeeded: {spot.config.id}")
                return result

            except ChessEngineTimeoutError as e:
                logger.warning(
                    f"Spot {spot.config.id} timed out after {self.timeout}s "
                    f"(attempt {attempts}/{max_attempts})"
                )
                errors.append(f"{spot.config.id}: timeout")
                # Continue to next spot

            except ChessEngineError as e:
                logger.warning(
                    f"Spot {spot.config.id} failed: {e} "
                    f"(attempt {attempts}/{max_attempts})"
                )
                errors.append(f"{spot.config.id}: {str(e)}")
                # Continue to next spot

            except Exception as e:
                logger.error(
                    f"Unexpected error from spot {spot.config.id}: {e} "
                    f"(attempt {attempts}/{max_attempts})"
                )
                errors.append(f"{spot.config.id}: {str(e)}")
                # Continue to next spot

        # All spots failed
        error_summary = "; ".join(errors)
        logger.error(f"All spots failed after {attempts} attempts: {error_summary}")
        if settings.ENGINE_FALLBACK_MODE != "off":
            self.last_spot_id = "fallback"
            return analyze_legal_moves(fen, depth, multipv)
        raise ChessEngineError(
            f"All engine spots failed ({attempts} attempts): {error_summary}"
        )

    def get_spot_metrics(self):
        """
        Get metrics for all spots.

        Returns:
            List of (config, metrics) tuples
        """
        return self.pool.get_all_spots()

    def enable_spot(self, spot_id: str) -> bool:
        """Enable a spot."""
        return self.pool.enable_spot(spot_id)

    def disable_spot(self, spot_id: str) -> bool:
        """Disable a spot."""
        return self.pool.disable_spot(spot_id)
