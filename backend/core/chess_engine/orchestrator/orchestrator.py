"""Engine orchestrator - routes requests and handles failover."""
from typing import List
from core.chess_engine.schemas import EngineResult
from core.chess_engine.spot.models import SpotConfig
from core.chess_engine.orchestrator.pool import EngineSpotPool
from core.log.log_chess_engine import logger
from core.errors import ChessEngineError, ChessEngineTimeoutError


class EngineOrchestrator:
    """
    Orchestrates requests across multiple engine spots.
    Handles routing, retry, and failover.
    """

    def __init__(self, spot_configs: List[SpotConfig] = None, timeout: int = 30, max_retries: int = 2):
        """
        Initialize orchestrator.

        Args:
            spot_configs: List of spot configurations (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries (total attempts = max_retries + 1)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.pool = EngineSpotPool(timeout=timeout)

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
