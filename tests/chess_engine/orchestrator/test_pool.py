"""Tests for EngineSpotPool."""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "backend"))

from core.chess_engine.orchestrator.pool import EngineSpotPool
from core.chess_engine.spot.models import SpotConfig, SpotStatus


class TestEngineSpotPool:
    """Test EngineSpotPool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pool = EngineSpotPool(timeout=30)

    def test_initialization(self):
        """Test pool initialization."""
        assert self.pool.timeout == 30
        assert len(self.pool.spots) == 0
        assert self.pool.selector is not None

    def test_register_single_spot(self):
        """Test registering a single spot."""
        config = SpotConfig(id="spot1", url="http://localhost:8001")
        spot = self.pool.register_spot(config)

        assert spot is not None
        assert spot.config.id == "spot1"
        assert self.pool.get_spot_count() == 1

    def test_register_multiple_spots(self):
        """Test registering multiple spots."""
        configs = [
            SpotConfig(id="spot1", url="http://localhost:8001"),
            SpotConfig(id="spot2", url="http://localhost:8002"),
            SpotConfig(id="spot3", url="http://localhost:8003"),
        ]
        self.pool.register_spots(configs)

        assert self.pool.get_spot_count() == 3
        assert self.pool.get_spot("spot1") is not None
        assert self.pool.get_spot("spot2") is not None
        assert self.pool.get_spot("spot3") is not None

    def test_register_duplicate_spot(self):
        """Test registering duplicate spot replaces existing."""
        config1 = SpotConfig(id="spot1", url="http://localhost:8001")
        config2 = SpotConfig(id="spot1", url="http://localhost:9999")

        spot1 = self.pool.register_spot(config1)
        spot2 = self.pool.register_spot(config2)

        assert self.pool.get_spot_count() == 1
        assert spot2.config.url == "http://localhost:9999"

    def test_get_spot_existing(self):
        """Test getting an existing spot."""
        config = SpotConfig(id="spot1", url="http://localhost:8001")
        self.pool.register_spot(config)

        spot = self.pool.get_spot("spot1")
        assert spot is not None
        assert spot.config.id == "spot1"

    def test_get_spot_nonexistent(self):
        """Test getting a non-existent spot."""
        spot = self.pool.get_spot("nonexistent")
        assert spot is None

    def test_get_all_spots(self):
        """Test getting all spots."""
        configs = [
            SpotConfig(id="spot1", url="http://localhost:8001"),
            SpotConfig(id="spot2", url="http://localhost:8002"),
        ]
        self.pool.register_spots(configs)

        all_spots = self.pool.get_all_spots()
        assert len(all_spots) == 2
        # Each item should be (config, metrics) tuple
        assert all(len(item) == 2 for item in all_spots)
        assert all(isinstance(item[0], SpotConfig) for item in all_spots)

    def test_get_best_spot_single(self):
        """Test getting best spot with single healthy spot."""
        config = SpotConfig(id="spot1", url="http://localhost:8001")
        self.pool.register_spot(config)

        # Mark as healthy
        spot = self.pool.get_spot("spot1")
        spot.metrics.status = SpotStatus.HEALTHY

        best = self.pool.get_best_spot()
        assert best is not None
        assert best.config.id == "spot1"

    def test_get_best_spot_multiple(self):
        """Test getting best spot with multiple spots."""
        configs = [
            SpotConfig(id="low-pri", url="http://localhost:8001", priority=50),
            SpotConfig(id="high-pri", url="http://localhost:8002", priority=150),
            SpotConfig(id="med-pri", url="http://localhost:8003", priority=100),
        ]
        self.pool.register_spots(configs)

        # Mark all as healthy
        for spot_id in ["low-pri", "high-pri", "med-pri"]:
            self.pool.get_spot(spot_id).metrics.status = SpotStatus.HEALTHY

        best = self.pool.get_best_spot()
        assert best is not None
        assert best.config.id == "high-pri"  # Highest priority

    def test_get_best_spot_none_available(self):
        """Test getting best spot when none are available."""
        config = SpotConfig(id="spot1", url="http://localhost:8001")
        self.pool.register_spot(config)

        # Mark as DOWN
        self.pool.get_spot("spot1").metrics.status = SpotStatus.DOWN

        best = self.pool.get_best_spot()
        assert best is None

    def test_get_best_spot_no_spots(self):
        """Test getting best spot with no registered spots."""
        best = self.pool.get_best_spot()
        assert best is None

    def test_get_usable_spots(self):
        """Test getting usable spots in priority order."""
        configs = [
            SpotConfig(id="spot1", url="http://localhost:8001", priority=50),
            SpotConfig(id="spot2", url="http://localhost:8002", priority=150),
            SpotConfig(id="spot3", url="http://localhost:8003", priority=100),
        ]
        self.pool.register_spots(configs)

        # Mark all as healthy
        for spot_id in ["spot1", "spot2", "spot3"]:
            self.pool.get_spot(spot_id).metrics.status = SpotStatus.HEALTHY

        usable = self.pool.get_usable_spots()
        assert len(usable) == 3
        # Should be in priority order
        assert usable[0].config.id == "spot2"  # priority 150
        assert usable[1].config.id == "spot3"  # priority 100
        assert usable[2].config.id == "spot1"  # priority 50

    def test_get_usable_spots_excludes_down(self):
        """Test that usable spots excludes DOWN spots."""
        configs = [
            SpotConfig(id="healthy", url="http://localhost:8001"),
            SpotConfig(id="down", url="http://localhost:8002"),
            SpotConfig(id="degraded", url="http://localhost:8003"),
        ]
        self.pool.register_spots(configs)

        self.pool.get_spot("healthy").metrics.status = SpotStatus.HEALTHY
        self.pool.get_spot("down").metrics.status = SpotStatus.DOWN
        self.pool.get_spot("degraded").metrics.status = SpotStatus.DEGRADED

        usable = self.pool.get_usable_spots()
        assert len(usable) == 2
        spot_ids = [spot.config.id for spot in usable]
        assert "healthy" in spot_ids
        assert "degraded" in spot_ids
        assert "down" not in spot_ids

    def test_enable_spot(self):
        """Test enabling a spot."""
        config = SpotConfig(id="spot1", url="http://localhost:8001", enabled=False)
        self.pool.register_spot(config)

        assert self.pool.get_spot("spot1").config.enabled is False

        result = self.pool.enable_spot("spot1")
        assert result is True
        assert self.pool.get_spot("spot1").config.enabled is True

    def test_enable_nonexistent_spot(self):
        """Test enabling a non-existent spot."""
        result = self.pool.enable_spot("nonexistent")
        assert result is False

    def test_disable_spot(self):
        """Test disabling a spot."""
        config = SpotConfig(id="spot1", url="http://localhost:8001", enabled=True)
        self.pool.register_spot(config)

        assert self.pool.get_spot("spot1").config.enabled is True

        result = self.pool.disable_spot("spot1")
        assert result is True
        assert self.pool.get_spot("spot1").config.enabled is False

    def test_disable_nonexistent_spot(self):
        """Test disabling a non-existent spot."""
        result = self.pool.disable_spot("nonexistent")
        assert result is False

    def test_spot_count(self):
        """Test spot count tracking."""
        assert self.pool.get_spot_count() == 0

        self.pool.register_spot(SpotConfig(id="spot1", url="http://localhost:8001"))
        assert self.pool.get_spot_count() == 1

        self.pool.register_spot(SpotConfig(id="spot2", url="http://localhost:8002"))
        assert self.pool.get_spot_count() == 2

        # Registering duplicate doesn't increase count
        self.pool.register_spot(SpotConfig(id="spot1", url="http://localhost:9999"))
        assert self.pool.get_spot_count() == 2

    def test_pool_with_custom_timeout(self):
        """Test pool with custom timeout."""
        pool = EngineSpotPool(timeout=10)
        config = SpotConfig(id="spot1", url="http://localhost:8001")
        spot = pool.register_spot(config)

        assert pool.timeout == 10
        assert spot.timeout == 10


if __name__ == "__main__":
    # Simple test runner
    test_class = TestEngineSpotPool()
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
