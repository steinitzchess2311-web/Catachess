"""Spot selection algorithm."""
from typing import List, Tuple, Optional
from core.chess_engine.spot.models import SpotConfig, SpotMetrics, SpotStatus


class SpotSelector:
    """Selects the best spot for a request."""

    def select_best(
        self,
        spots: List[Tuple[SpotConfig, SpotMetrics]],
    ) -> Optional[SpotConfig]:
        """
        Select best available spot.

        Algorithm:
        1. Filter by enabled status
        2. Filter by health status (HEALTHY > DEGRADED > DOWN)
        3. Sort by priority (desc) → latency (asc) → success_rate (desc)
        4. Return top spot

        Returns None if no usable spots.
        """
        # Filter out disabled spots
        enabled_spots = [(cfg, m) for cfg, m in spots if cfg.enabled]
        if not enabled_spots:
            return None

        # Filter by status priority: HEALTHY first, then DEGRADED
        healthy = [(cfg, m) for cfg, m in enabled_spots if m.status == SpotStatus.HEALTHY]
        degraded = [(cfg, m) for cfg, m in enabled_spots if m.status == SpotStatus.DEGRADED]

        # Use healthy spots if available, otherwise degraded
        candidates = healthy or degraded
        if not candidates:
            return None

        # Sort by: priority DESC, latency ASC, success_rate DESC
        candidates.sort(
            key=lambda x: (
                -x[0].priority,          # Higher priority first (negative for DESC)
                x[1].avg_latency_ms,     # Lower latency first
                -x[1].success_rate,      # Higher success rate first (negative for DESC)
            )
        )

        return candidates[0][0]  # Return SpotConfig

    def select_all_usable(
        self,
        spots: List[Tuple[SpotConfig, SpotMetrics]],
    ) -> List[SpotConfig]:
        """
        Get all usable spots in priority order.
        Used for failover - returns list of spots to try in order.
        """
        # Filter enabled spots
        enabled_spots = [(cfg, m) for cfg, m in spots if cfg.enabled]

        # Get healthy and degraded spots (exclude DOWN and UNKNOWN)
        usable = [
            (cfg, m) for cfg, m in enabled_spots
            if m.status in (SpotStatus.HEALTHY, SpotStatus.DEGRADED)
        ]

        if not usable:
            return []

        # Sort by priority DESC, latency ASC, success_rate DESC
        usable.sort(
            key=lambda x: (
                -x[0].priority,
                x[1].avg_latency_ms,
                -x[1].success_rate,
            )
        )

        return [cfg for cfg, _ in usable]
