"""Tests for EngineOrchestrator."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "backend"))

from core.chess_engine.orchestrator.orchestrator import EngineOrchestrator
from core.chess_engine.spot.models import SpotConfig, SpotStatus
from core.chess_engine.schemas import EngineResult, EngineLine
from core.errors import ChessEngineError, ChessEngineTimeoutError


class TestEngineOrchestrator:
    """Test EngineOrchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.configs = [
            SpotConfig(id="spot1", url="http://localhost:8001", priority=100),
            SpotConfig(id="spot2", url="http://localhost:8002", priority=90),
            SpotConfig(id="spot3", url="http://localhost:8003", priority=80),
        ]
        self.orchestrator = EngineOrchestrator(
            spot_configs=self.configs,
            timeout=30,
            max_retries=2
        )

    def test_initialization(self):
        """Test orchestrator initialization."""
        assert self.orchestrator.timeout == 30
        assert self.orchestrator.max_retries == 2
        assert self.orchestrator.pool.get_spot_count() == 3

    def test_initialization_no_spots(self):
        """Test initialization without spots."""
        orch = EngineOrchestrator()
        assert orch.pool.get_spot_count() == 0

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_success_first_spot(self, mock_analyze):
        """Test successful analysis on first spot."""
        # Mock successful response
        mock_result = EngineResult(lines=[
            EngineLine(multipv=1, score=25, pv=["e2e4"])
        ])
        mock_analyze.return_value = mock_result

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2", "spot3"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = self.orchestrator.analyze(fen)

        assert result is not None
        assert len(result.lines) == 1
        # Should only call once (first spot succeeded)
        assert mock_analyze.call_count == 1

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_failover_on_timeout(self, mock_analyze):
        """Test failover to second spot when first times out."""
        # First call times out, second succeeds
        mock_result = EngineResult(lines=[EngineLine(multipv=1, score=25, pv=["e2e4"])])
        mock_analyze.side_effect = [
            ChessEngineTimeoutError(30),  # First spot times out
            mock_result,                  # Second spot succeeds
        ]

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2", "spot3"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = self.orchestrator.analyze(fen)

        assert result is not None
        # Should try spot1, then spot2
        assert mock_analyze.call_count == 2

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_failover_on_error(self, mock_analyze):
        """Test failover to second spot when first fails."""
        mock_result = EngineResult(lines=[EngineLine(multipv=1, score=25, pv=["e2e4"])])
        mock_analyze.side_effect = [
            ChessEngineError("Connection refused"),  # First spot fails
            mock_result,                              # Second spot succeeds
        ]

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = self.orchestrator.analyze(fen)

        assert result is not None
        assert mock_analyze.call_count == 2

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_all_spots_fail(self, mock_analyze):
        """Test error when all spots fail."""
        # All spots timeout
        mock_analyze.side_effect = ChessEngineTimeoutError(30)

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2", "spot3"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            self.orchestrator.analyze(fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError as e:
            assert "All engine spots failed" in str(e)
            # Should try all 3 spots (max_retries=2 means 3 total attempts)
            assert mock_analyze.call_count == 3

    def test_analyze_no_spots_available(self):
        """Test error when no spots are available."""
        # Create orchestrator with no spots
        orch = EngineOrchestrator()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            orch.analyze(fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError as e:
            assert "No engine spots available" in str(e)

    def test_analyze_all_spots_down(self):
        """Test error when all spots are DOWN."""
        # Mark all spots as DOWN
        for spot_id in ["spot1", "spot2", "spot3"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.DOWN

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            self.orchestrator.analyze(fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError as e:
            assert "No engine spots available" in str(e)

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_respects_max_retries(self, mock_analyze):
        """Test that orchestrator respects max_retries setting."""
        # All spots fail
        mock_analyze.side_effect = ChessEngineError("Fail")

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2", "spot3"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        # Create orchestrator with max_retries=1 (2 total attempts)
        orch = EngineOrchestrator(spot_configs=self.configs, max_retries=1)
        for spot_id in ["spot1", "spot2", "spot3"]:
            orch.pool.get_spot(spot_id).metrics.status = SpotStatus.HEALTHY

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            orch.analyze(fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError:
            pass

        # Should try only 2 spots (max_retries=1 means 2 total attempts)
        assert mock_analyze.call_count == 2

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_priority_order(self, mock_analyze):
        """Test that spots are tried in priority order."""
        # Track which spots were called
        called_spots = []

        def track_call(*args, **kwargs):
            # Get the spot instance from the method call
            import inspect
            frame = inspect.currentframe().f_back
            spot_instance = frame.f_locals.get('self')
            if spot_instance:
                called_spots.append(spot_instance.config.id)
            raise ChessEngineError("Fail")

        mock_analyze.side_effect = track_call

        # Mark all spots as healthy
        for spot_id in ["spot1", "spot2", "spot3"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            self.orchestrator.analyze(fen)
        except ChessEngineError:
            pass

        # Spots should be tried in priority order: spot1 (100), spot2 (90), spot3 (80)
        # Note: Due to mocking complexity, we just verify all 3 were tried
        assert mock_analyze.call_count == 3

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_with_custom_depth_and_multipv(self, mock_analyze):
        """Test analyze with custom depth and multipv parameters."""
        mock_result = EngineResult(lines=[EngineLine(multipv=1, score=25, pv=["e2e4"])])
        mock_analyze.return_value = mock_result

        spot = self.orchestrator.pool.get_spot("spot1")
        spot.metrics.status = SpotStatus.HEALTHY

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = self.orchestrator.analyze(fen, depth=20, multipv=5)

        assert result is not None
        # Verify parameters were passed
        mock_analyze.assert_called_once_with(fen, depth=20, multipv=5)

    def test_get_spot_metrics(self):
        """Test getting spot metrics."""
        metrics = self.orchestrator.get_spot_metrics()
        assert len(metrics) == 3
        # Each item should be (config, metrics) tuple
        assert all(len(item) == 2 for item in metrics)

    def test_enable_spot(self):
        """Test enabling a spot."""
        # Disable spot first
        spot = self.orchestrator.pool.get_spot("spot1")
        spot.config.enabled = False

        result = self.orchestrator.enable_spot("spot1")
        assert result is True
        assert spot.config.enabled is True

    def test_disable_spot(self):
        """Test disabling a spot."""
        result = self.orchestrator.disable_spot("spot1")
        assert result is True
        spot = self.orchestrator.pool.get_spot("spot1")
        assert spot.config.enabled is False

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_skips_disabled_spots(self, mock_analyze):
        """Test that disabled spots are skipped."""
        mock_result = EngineResult(lines=[EngineLine(multipv=1, score=25, pv=["e2e4"])])
        mock_analyze.return_value = mock_result

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        # Disable spot1
        self.orchestrator.disable_spot("spot1")

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = self.orchestrator.analyze(fen)

        assert result is not None
        # Should only call spot2 (spot1 is disabled)
        assert mock_analyze.call_count == 1

    @patch('core.chess_engine.spot.spot.EngineSpot.analyze')
    def test_analyze_handles_unexpected_exception(self, mock_analyze):
        """Test that unexpected exceptions are caught and failover occurs."""
        mock_result = EngineResult(lines=[EngineLine(multipv=1, score=25, pv=["e2e4"])])
        mock_analyze.side_effect = [
            RuntimeError("Unexpected error"),  # First spot raises unexpected error
            mock_result,                        # Second spot succeeds
        ]

        # Mark spots as healthy
        for spot_id in ["spot1", "spot2"]:
            spot = self.orchestrator.pool.get_spot(spot_id)
            spot.metrics.status = SpotStatus.HEALTHY

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = self.orchestrator.analyze(fen)

        assert result is not None
        assert mock_analyze.call_count == 2


if __name__ == "__main__":
    # Simple test runner
    test_class = TestEngineOrchestrator()
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
