"""Tests for SpotSelector."""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "backend"))

from core.chess_engine.orchestrator.selector import SpotSelector
from core.chess_engine.spot.models import SpotConfig, SpotMetrics, SpotStatus


class TestSpotSelector:
    """Test SpotSelector algorithm."""

    def setup_method(self):
        """Set up test fixtures."""
        self.selector = SpotSelector()

    def test_select_single_healthy_spot(self):
        """Test selection with single healthy spot."""
        config = SpotConfig(id="spot1", url="http://localhost:8001")
        metrics = SpotMetrics(status=SpotStatus.HEALTHY)
        spots = [(config, metrics)]

        selected = self.selector.select_best(spots)
        assert selected is not None
        assert selected.id == "spot1"

    def test_select_no_spots(self):
        """Test selection with no spots."""
        selected = self.selector.select_best([])
        assert selected is None

    def test_select_all_down_spots(self):
        """Test selection with all DOWN spots."""
        spots = [
            (SpotConfig(id="spot1", url="http://localhost:8001"),
             SpotMetrics(status=SpotStatus.DOWN)),
            (SpotConfig(id="spot2", url="http://localhost:8002"),
             SpotMetrics(status=SpotStatus.DOWN)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is None

    def test_select_healthy_over_degraded(self):
        """Test that HEALTHY spots are preferred over DEGRADED."""
        spots = [
            (SpotConfig(id="degraded", url="http://localhost:8001", priority=150),
             SpotMetrics(status=SpotStatus.DEGRADED, avg_latency_ms=50)),
            (SpotConfig(id="healthy", url="http://localhost:8002", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=100)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is not None
        assert selected.id == "healthy"  # HEALTHY preferred despite lower priority

    def test_select_by_priority(self):
        """Test selection by priority when health is equal."""
        spots = [
            (SpotConfig(id="low-pri", url="http://localhost:8001", priority=50),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=100)),
            (SpotConfig(id="high-pri", url="http://localhost:8002", priority=150),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=100)),
            (SpotConfig(id="med-pri", url="http://localhost:8003", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=100)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is not None
        assert selected.id == "high-pri"

    def test_select_by_latency(self):
        """Test selection by latency when priority is equal."""
        spots = [
            (SpotConfig(id="slow", url="http://localhost:8001", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=200)),
            (SpotConfig(id="fast", url="http://localhost:8002", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=50)),
            (SpotConfig(id="medium", url="http://localhost:8003", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=100)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is not None
        assert selected.id == "fast"

    def test_select_by_success_rate(self):
        """Test selection by success rate when priority and latency are equal."""
        spots = [
            (SpotConfig(id="unreliable", url="http://localhost:8001", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=100, success_rate=0.5)),
            (SpotConfig(id="reliable", url="http://localhost:8002", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=100, success_rate=0.99)),
            (SpotConfig(id="medium", url="http://localhost:8003", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=100, success_rate=0.8)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is not None
        assert selected.id == "reliable"

    def test_select_complex_sorting(self):
        """Test complex sorting with multiple criteria."""
        spots = [
            # Priority 150, fast but unreliable
            (SpotConfig(id="spot1", url="http://localhost:8001", priority=150),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=50, success_rate=0.7)),
            # Priority 100, slow but reliable
            (SpotConfig(id="spot2", url="http://localhost:8002", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=200, success_rate=0.99)),
            # Priority 150, slow but very reliable
            (SpotConfig(id="spot3", url="http://localhost:8003", priority=150),
             SpotMetrics(status=SpotStatus.HEALTHY, avg_latency_ms=150, success_rate=0.99)),
        ]

        selected = self.selector.select_best(spots)
        # Should select spot1: priority 150 (highest), latency 50 (lowest among 150)
        assert selected is not None
        assert selected.id == "spot1"

    def test_select_degraded_when_no_healthy(self):
        """Test that DEGRADED spots are used when no HEALTHY spots."""
        spots = [
            (SpotConfig(id="degraded1", url="http://localhost:8001", priority=100),
             SpotMetrics(status=SpotStatus.DEGRADED, avg_latency_ms=100)),
            (SpotConfig(id="degraded2", url="http://localhost:8002", priority=150),
             SpotMetrics(status=SpotStatus.DEGRADED, avg_latency_ms=50)),
            (SpotConfig(id="down", url="http://localhost:8003"),
             SpotMetrics(status=SpotStatus.DOWN)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is not None
        assert selected.id == "degraded2"  # Higher priority

    def test_select_ignores_unknown_status(self):
        """Test that UNKNOWN status spots are not selected."""
        spots = [
            (SpotConfig(id="unknown", url="http://localhost:8001", priority=200),
             SpotMetrics(status=SpotStatus.UNKNOWN)),
            (SpotConfig(id="healthy", url="http://localhost:8002", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is not None
        assert selected.id == "healthy"

    def test_select_ignores_disabled_spots(self):
        """Test that disabled spots are not selected."""
        spots = [
            (SpotConfig(id="disabled", url="http://localhost:8001", priority=200, enabled=False),
             SpotMetrics(status=SpotStatus.HEALTHY)),
            (SpotConfig(id="enabled", url="http://localhost:8002", priority=100, enabled=True),
             SpotMetrics(status=SpotStatus.HEALTHY)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is not None
        assert selected.id == "enabled"

    def test_select_all_disabled(self):
        """Test selection with all disabled spots."""
        spots = [
            (SpotConfig(id="spot1", url="http://localhost:8001", enabled=False),
             SpotMetrics(status=SpotStatus.HEALTHY)),
            (SpotConfig(id="spot2", url="http://localhost:8002", enabled=False),
             SpotMetrics(status=SpotStatus.HEALTHY)),
        ]

        selected = self.selector.select_best(spots)
        assert selected is None

    def test_select_all_usable_empty(self):
        """Test select_all_usable with no spots."""
        result = self.selector.select_all_usable([])
        assert result == []

    def test_select_all_usable_single_spot(self):
        """Test select_all_usable with single spot."""
        spots = [
            (SpotConfig(id="spot1", url="http://localhost:8001"),
             SpotMetrics(status=SpotStatus.HEALTHY)),
        ]

        result = self.selector.select_all_usable(spots)
        assert len(result) == 1
        assert result[0].id == "spot1"

    def test_select_all_usable_sorted(self):
        """Test select_all_usable returns spots in priority order."""
        spots = [
            (SpotConfig(id="low", url="http://localhost:8001", priority=50),
             SpotMetrics(status=SpotStatus.HEALTHY)),
            (SpotConfig(id="high", url="http://localhost:8002", priority=150),
             SpotMetrics(status=SpotStatus.HEALTHY)),
            (SpotConfig(id="med", url="http://localhost:8003", priority=100),
             SpotMetrics(status=SpotStatus.HEALTHY)),
        ]

        result = self.selector.select_all_usable(spots)
        assert len(result) == 3
        assert result[0].id == "high"
        assert result[1].id == "med"
        assert result[2].id == "low"

    def test_select_all_usable_excludes_down(self):
        """Test select_all_usable excludes DOWN spots."""
        spots = [
            (SpotConfig(id="healthy", url="http://localhost:8001"),
             SpotMetrics(status=SpotStatus.HEALTHY)),
            (SpotConfig(id="down", url="http://localhost:8002"),
             SpotMetrics(status=SpotStatus.DOWN)),
            (SpotConfig(id="degraded", url="http://localhost:8003"),
             SpotMetrics(status=SpotStatus.DEGRADED)),
        ]

        result = self.selector.select_all_usable(spots)
        assert len(result) == 2
        spot_ids = [spot.id for spot in result]
        assert "healthy" in spot_ids
        assert "degraded" in spot_ids
        assert "down" not in spot_ids

    def test_select_all_usable_excludes_disabled(self):
        """Test select_all_usable excludes disabled spots."""
        spots = [
            (SpotConfig(id="enabled", url="http://localhost:8001", enabled=True),
             SpotMetrics(status=SpotStatus.HEALTHY)),
            (SpotConfig(id="disabled", url="http://localhost:8002", enabled=False),
             SpotMetrics(status=SpotStatus.HEALTHY)),
        ]

        result = self.selector.select_all_usable(spots)
        assert len(result) == 1
        assert result[0].id == "enabled"


if __name__ == "__main__":
    # Simple test runner
    test_class = TestSpotSelector()
    test_methods = [
        method for method in dir(test_class)
        if method.startswith('test_') and callable(getattr(test_class, method))
    ]

    passed = 0
    failed = 0

    for method_name in test_methods:
        try:
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            print(f"✓ {method_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
