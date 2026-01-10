"""Integration tests for multi-spot engine system."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from core.chess_engine.orchestrator.orchestrator import EngineOrchestrator
from core.chess_engine.spot.models import SpotConfig, SpotStatus
from core.chess_engine.schemas import EngineResult, EngineLine
from core.errors import ChessEngineError, ChessEngineTimeoutError


class TestMultiSpotIntegration:
    """Integration tests for multi-spot engine system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.mock_sse_response = b"""data: info depth 15 multipv 1 score cp 25 pv e2e4 e7e5
data: info depth 15 multipv 2 score cp 15 pv d2d4 d7d5
data: info depth 15 multipv 3 score mate 3 pv f2f4 e7e5 f4e5
"""

    def create_orchestrator_with_spots(self, num_spots=3):
        """Helper to create orchestrator with test spots."""
        configs = [
            SpotConfig(
                id=f"spot{i+1}",
                url=f"http://localhost:800{i+1}",
                priority=100 - (i * 10)
            )
            for i in range(num_spots)
        ]
        return EngineOrchestrator(spot_configs=configs, timeout=30, max_retries=2)

    @patch('requests.get')
    def test_end_to_end_successful_analysis(self, mock_get):
        """Test complete flow: orchestrator -> pool -> selector -> spot -> analyze."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = self.mock_sse_response.split(b'\n')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create orchestrator
        orchestrator = self.create_orchestrator_with_spots(num_spots=2)

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2"]:
            spot = orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        # Analyze
        result = orchestrator.analyze(self.test_fen, depth=15, multipv=3)

        # Verify result
        assert isinstance(result, EngineResult)
        assert len(result.lines) == 3
        assert result.lines[0].multipv == 1
        assert result.lines[0].score == 25
        assert result.lines[0].pv == ['e2e4', 'e7e5']

        # Verify metrics updated
        spot1 = orchestrator.pool.get_spot("spot1")
        assert spot1.metrics.total_requests == 1
        assert spot1.metrics.failure_count == 0
        assert spot1.metrics.status == SpotStatus.HEALTHY

        # Verify only one spot was called (first succeeded)
        assert mock_get.call_count == 1

    @patch('requests.get')
    def test_end_to_end_failover_scenario(self, mock_get):
        """Test failover: first spot times out, second succeeds."""
        import requests

        # First call times out, second succeeds
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.iter_lines.return_value = self.mock_sse_response.split(b'\n')
        mock_success_response.raise_for_status = Mock()

        mock_get.side_effect = [
            requests.exceptions.Timeout("Timeout"),  # First spot times out
            mock_success_response,                   # Second spot succeeds
        ]

        # Create orchestrator
        orchestrator = self.create_orchestrator_with_spots(num_spots=2)

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2"]:
            spot = orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        # Analyze
        result = orchestrator.analyze(self.test_fen)

        # Verify result
        assert isinstance(result, EngineResult)
        assert len(result.lines) > 0

        # Verify failover occurred
        assert mock_get.call_count == 2

        # Verify spot1 metrics (failed)
        spot1 = orchestrator.pool.get_spot("spot1")
        assert spot1.metrics.failure_count == 1

        # Verify spot2 metrics (succeeded)
        spot2 = orchestrator.pool.get_spot("spot2")
        assert spot2.metrics.total_requests == 1
        assert spot2.metrics.failure_count == 0

    @patch('requests.get')
    def test_end_to_end_all_spots_down(self, mock_get):
        """Test scenario where all spots are DOWN (not usable)."""
        # Create orchestrator
        orchestrator = self.create_orchestrator_with_spots(num_spots=3)

        # Mark all spots as DOWN
        for spot_id in ["spot1", "spot2", "spot3"]:
            spot = orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.DOWN

        # Analyze should fail
        try:
            orchestrator.analyze(self.test_fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError as e:
            assert "No engine spots available" in str(e)

        # Verify no HTTP calls were made (spots were filtered before trying)
        assert mock_get.call_count == 0

    @patch('requests.get')
    def test_end_to_end_priority_ordering(self, mock_get):
        """Test that spots are tried in priority order."""
        import requests

        # All spots fail except the last
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.iter_lines.return_value = self.mock_sse_response.split(b'\n')
        mock_success_response.raise_for_status = Mock()

        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Fail"),  # spot1 (priority 100)
            requests.exceptions.ConnectionError("Fail"),  # spot2 (priority 90)
            mock_success_response,                        # spot3 (priority 80)
        ]

        # Create orchestrator with 3 spots
        orchestrator = self.create_orchestrator_with_spots(num_spots=3)

        # Mark all as healthy
        for spot_id in ["spot1", "spot2", "spot3"]:
            spot = orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        # Analyze
        result = orchestrator.analyze(self.test_fen)

        # Verify all 3 were tried in order
        assert mock_get.call_count == 3

        # Verify spot3 succeeded
        spot3 = orchestrator.pool.get_spot("spot3")
        assert spot3.metrics.total_requests == 1
        assert spot3.metrics.failure_count == 0

    @patch('requests.get')
    def test_end_to_end_disabled_spot_skipped(self, mock_get):
        """Test that disabled spots are skipped."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = self.mock_sse_response.split(b'\n')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create orchestrator
        orchestrator = self.create_orchestrator_with_spots(num_spots=2)

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2"]:
            spot = orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        # Disable spot1 (highest priority)
        orchestrator.disable_spot("spot1")

        # Analyze
        result = orchestrator.analyze(self.test_fen)

        # Verify result
        assert isinstance(result, EngineResult)

        # Verify only spot2 was called (spot1 disabled)
        assert mock_get.call_count == 1

        # Verify spot2 was used
        spot2 = orchestrator.pool.get_spot("spot2")
        assert spot2.metrics.total_requests == 1

        # Verify spot1 was not used
        spot1 = orchestrator.pool.get_spot("spot1")
        assert spot1.metrics.total_requests == 0

    @patch('requests.get')
    def test_end_to_end_metrics_accumulation(self, mock_get):
        """Test that metrics accumulate correctly over multiple requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = self.mock_sse_response.split(b'\n')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create orchestrator
        orchestrator = self.create_orchestrator_with_spots(num_spots=1)

        # Mark spot as healthy
        spot = orchestrator.pool.get_spot("spot1")
        spot.metrics.status = SpotStatus.HEALTHY

        # Make 5 successful requests
        for i in range(5):
            result = orchestrator.analyze(self.test_fen)
            assert isinstance(result, EngineResult)

        # Verify metrics
        assert spot.metrics.total_requests == 5
        assert spot.metrics.failure_count == 0
        assert spot.metrics.success_rate == 1.0
        assert spot.metrics.avg_latency_ms > 0

    @patch('requests.get')
    def test_end_to_end_mixed_success_and_failure(self, mock_get):
        """Test metrics with mixed successes and failures."""
        import requests

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.iter_lines.return_value = self.mock_sse_response.split(b'\n')
        mock_success.raise_for_status = Mock()

        # Pattern: success, fail, success, success
        mock_get.side_effect = [
            mock_success,
            requests.exceptions.ConnectionError("Fail"),
            mock_success,
            mock_success,
        ]

        # Create orchestrator with 1 spot
        orchestrator = self.create_orchestrator_with_spots(num_spots=1)
        spot = orchestrator.pool.get_spot("spot1")
        spot.metrics.status = SpotStatus.HEALTHY

        # Make 4 requests (1 will fail)
        success_count = 0
        for i in range(4):
            try:
                result = orchestrator.analyze(self.test_fen)
                success_count += 1
            except ChessEngineError:
                pass

        # Verify metrics
        assert success_count == 3
        assert spot.metrics.total_requests == 4
        assert spot.metrics.failure_count == 1
        assert spot.metrics.success_rate == 0.75

    @patch('requests.get')
    def test_end_to_end_respects_max_retries(self, mock_get):
        """Test that max_retries is respected."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        # Create orchestrator with max_retries=1 (2 total attempts)
        configs = [
            SpotConfig(id=f"spot{i+1}", url=f"http://localhost:800{i+1}")
            for i in range(3)
        ]
        orchestrator = EngineOrchestrator(
            spot_configs=configs,
            timeout=30,
            max_retries=1  # Only 2 total attempts
        )

        # Mark all as healthy
        for i in range(3):
            spot = orchestrator.pool.get_spot(f"spot{i+1}")
            spot.metrics.status = SpotStatus.HEALTHY

        # Analyze should fail
        try:
            orchestrator.analyze(self.test_fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError:
            pass

        # Should only try 2 spots (max_retries=1)
        assert mock_get.call_count == 2


if __name__ == "__main__":
    # Simple test runner
    test_class = TestMultiSpotIntegration()
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
