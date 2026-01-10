"""Tests for spot models."""
import pytest
from datetime import datetime
from backend.core.chess_engine.spot.models import SpotStatus, SpotConfig, SpotMetrics


class TestSpotStatus:
    """Test SpotStatus enum."""

    def test_status_values(self):
        """Test all status enum values."""
        assert SpotStatus.HEALTHY == "healthy"
        assert SpotStatus.DEGRADED == "degraded"
        assert SpotStatus.DOWN == "down"
        assert SpotStatus.UNKNOWN == "unknown"

    def test_status_comparison(self):
        """Test status can be compared."""
        assert SpotStatus.HEALTHY == SpotStatus.HEALTHY
        assert SpotStatus.HEALTHY != SpotStatus.DOWN


class TestSpotConfig:
    """Test SpotConfig model."""

    def test_minimal_config(self):
        """Test config with minimal required fields."""
        config = SpotConfig(id="test-spot", url="http://localhost:8001")
        assert config.id == "test-spot"
        assert config.url == "http://localhost:8001"
        assert config.region == "unknown"
        assert config.priority == 100
        assert config.enabled is True

    def test_full_config(self):
        """Test config with all fields."""
        config = SpotConfig(
            id="cn-shanghai",
            url="http://192.168.40.33:8001",
            region="cn-east",
            priority=150,
            enabled=True
        )
        assert config.id == "cn-shanghai"
        assert config.url == "http://192.168.40.33:8001"
        assert config.region == "cn-east"
        assert config.priority == 150
        assert config.enabled is True

    def test_priority_validation(self):
        """Test priority field validation."""
        # Valid priorities
        config = SpotConfig(id="test", url="http://localhost", priority=0)
        assert config.priority == 0

        config = SpotConfig(id="test", url="http://localhost", priority=200)
        assert config.priority == 200

        # Invalid priorities
        with pytest.raises(Exception):  # Pydantic ValidationError
            SpotConfig(id="test", url="http://localhost", priority=-1)

        with pytest.raises(Exception):
            SpotConfig(id="test", url="http://localhost", priority=201)

    def test_disabled_spot(self):
        """Test disabled spot configuration."""
        config = SpotConfig(id="test", url="http://localhost", enabled=False)
        assert config.enabled is False


class TestSpotMetrics:
    """Test SpotMetrics model."""

    def test_initial_metrics(self):
        """Test initial metrics state."""
        metrics = SpotMetrics()
        assert metrics.status == SpotStatus.UNKNOWN
        assert metrics.avg_latency_ms == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.last_healthy_at is None
        assert metrics.failure_count == 0
        assert metrics.total_requests == 0

    def test_update_success_first_request(self):
        """Test update_success for first request."""
        metrics = SpotMetrics()
        metrics.update_success(latency_ms=100.0)

        assert metrics.total_requests == 1
        assert metrics.avg_latency_ms == 100.0
        assert metrics.success_rate == 1.0
        assert metrics.failure_count == 0
        assert metrics.status == SpotStatus.HEALTHY
        assert metrics.last_healthy_at is not None
        assert isinstance(metrics.last_healthy_at, datetime)

    def test_update_success_multiple_requests(self):
        """Test update_success with multiple requests."""
        metrics = SpotMetrics()

        # First request: 100ms
        metrics.update_success(100.0)
        assert metrics.avg_latency_ms == 100.0

        # Second request: 200ms -> avg = 150ms
        metrics.update_success(200.0)
        assert metrics.total_requests == 2
        assert metrics.avg_latency_ms == 150.0
        assert metrics.success_rate == 1.0

        # Third request: 150ms -> avg = (100+200+150)/3 = 150ms
        metrics.update_success(150.0)
        assert metrics.total_requests == 3
        assert metrics.avg_latency_ms == 150.0
        assert metrics.success_rate == 1.0

    def test_update_failure(self):
        """Test update_failure increments counters."""
        metrics = SpotMetrics()
        metrics.update_failure()

        assert metrics.total_requests == 1
        assert metrics.failure_count == 1
        assert metrics.success_rate == 0.0

    def test_mixed_success_and_failure(self):
        """Test metrics with mixed success and failure."""
        metrics = SpotMetrics()

        # 3 successes
        metrics.update_success(100.0)
        metrics.update_success(200.0)
        metrics.update_success(150.0)
        assert metrics.total_requests == 3
        assert metrics.success_rate == 1.0
        assert metrics.avg_latency_ms == 150.0

        # 1 failure -> success rate = 3/4 = 0.75
        metrics.update_failure()
        assert metrics.total_requests == 4
        assert metrics.failure_count == 1
        assert metrics.success_rate == 0.75

        # 1 more success -> success rate = 4/5 = 0.8
        metrics.update_success(100.0)
        assert metrics.total_requests == 5
        assert metrics.success_rate == 0.8

    def test_success_rate_calculation(self):
        """Test success rate calculation accuracy."""
        metrics = SpotMetrics()

        # 7 successes, 3 failures -> 70% success rate
        for _ in range(7):
            metrics.update_success(100.0)
        for _ in range(3):
            metrics.update_failure()

        assert metrics.total_requests == 10
        assert metrics.failure_count == 3
        assert metrics.success_rate == 0.7

    def test_update_success_updates_status(self):
        """Test that update_success sets status to HEALTHY."""
        metrics = SpotMetrics(status=SpotStatus.DEGRADED)
        metrics.update_success(100.0)
        assert metrics.status == SpotStatus.HEALTHY

    def test_update_failure_does_not_change_status(self):
        """Test that update_failure doesn't change status (managed by health monitor)."""
        metrics = SpotMetrics(status=SpotStatus.HEALTHY)
        metrics.update_failure()
        # Status should remain unchanged (health monitor manages it)
        assert metrics.status == SpotStatus.HEALTHY

    def test_last_healthy_timestamp_updates(self):
        """Test that last_healthy_at updates on success."""
        metrics = SpotMetrics()

        metrics.update_success(100.0)
        first_timestamp = metrics.last_healthy_at
        assert first_timestamp is not None

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        metrics.update_success(100.0)
        second_timestamp = metrics.last_healthy_at
        assert second_timestamp is not None
        assert second_timestamp >= first_timestamp
