"""Engine spot pool management."""
from typing import Dict, List, Tuple, Optional
from core.chess_engine.spot.spot import EngineSpot
from core.chess_engine.spot.models import SpotConfig, SpotMetrics
from core.chess_engine.orchestrator.selector import SpotSelector
from core.log.log_chess_engine import logger


class EngineSpotPool:
    """Manages a pool of engine spots."""

    def __init__(self, timeout: int = 30):
        """
        Initialize spot pool.

        Args:
            timeout: Default timeout for spot requests in seconds
        """
        self.timeout = timeout
        self.spots: Dict[str, EngineSpot] = {}
        self.selector = SpotSelector()
        self.health_monitor = None  # Will be set when health monitor is added
        logger.info(f"EngineSpotPool initialized with timeout={timeout}s")

    def register_spot(self, config: SpotConfig) -> EngineSpot:
        """
        Register a new spot in the pool.

        Args:
            config: Spot configuration

        Returns:
            The created EngineSpot instance
        """
        if config.id in self.spots:
            logger.warning(f"Spot {config.id} already registered, replacing")

        spot = EngineSpot(config, timeout=self.timeout)
        self.spots[config.id] = spot
        logger.info(f"Registered spot: {config.id} ({config.url})")
        return spot

    def register_spots(self, configs: List[SpotConfig]):
        """
        Register multiple spots.

        Args:
            configs: List of spot configurations
        """
        for config in configs:
            self.register_spot(config)
        logger.info(f"Registered {len(configs)} spots total")

    def get_spot(self, spot_id: str) -> Optional[EngineSpot]:
        """
        Get a spot by ID.

        Args:
            spot_id: Spot identifier

        Returns:
            EngineSpot instance or None if not found
        """
        return self.spots.get(spot_id)

    def get_all_spots(self) -> List[Tuple[SpotConfig, SpotMetrics]]:
        """
        Get all spots with their configs and metrics.

        Returns:
            List of (config, metrics) tuples
        """
        return [(spot.config, spot.metrics) for spot in self.spots.values()]

    def get_best_spot(self) -> Optional[EngineSpot]:
        """
        Get the best available spot.

        Returns:
            Best EngineSpot or None if no spots available
        """
        all_spots = self.get_all_spots()
        best_config = self.selector.select_best(all_spots)

        if best_config:
            return self.spots.get(best_config.id)
        return None

    def get_usable_spots(self) -> List[EngineSpot]:
        """
        Get all usable spots in priority order.

        Returns:
            List of EngineSpots in priority order for failover
        """
        all_spots = self.get_all_spots()
        usable_configs = self.selector.select_all_usable(all_spots)
        return [self.spots[config.id] for config in usable_configs]

    def enable_spot(self, spot_id: str) -> bool:
        """
        Enable a spot.

        Args:
            spot_id: Spot identifier

        Returns:
            True if spot was enabled, False if not found
        """
        spot = self.get_spot(spot_id)
        if spot:
            spot.config.enabled = True
            logger.info(f"Enabled spot: {spot_id}")
            return True
        logger.warning(f"Cannot enable spot: {spot_id} not found")
        return False

    def disable_spot(self, spot_id: str) -> bool:
        """
        Disable a spot.

        Args:
            spot_id: Spot identifier

        Returns:
            True if spot was disabled, False if not found
        """
        spot = self.get_spot(spot_id)
        if spot:
            spot.config.enabled = False
            logger.info(f"Disabled spot: {spot_id}")
            return True
        logger.warning(f"Cannot disable spot: {spot_id} not found")
        return False

    def get_spot_count(self) -> int:
        """Get total number of registered spots."""
        return len(self.spots)
