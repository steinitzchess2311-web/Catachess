"""Tests for EngineSpot client."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "backend"))

from core.chess_engine.spot.spot import EngineSpot
from core.chess_engine.spot.models import SpotConfig, SpotStatus
from core.chess_engine.schemas import EngineResult
from core.errors import ChessEngineError, ChessEngineTimeoutError


class TestEngineSpot:
    """Test EngineSpot client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = SpotConfig(
            id="test-spot",
            url="http://localhost:8001",
            region="test",
            priority=100
        )
        self.spot = EngineSpot(self.config, timeout=30)

    def test_initialization(self):
        """Test spot initialization."""
        assert self.spot.config.id == "test-spot"
        assert self.spot.config.url == "http://localhost:8001"
        assert self.spot.timeout == 30
        assert self.spot.metrics.status == SpotStatus.UNKNOWN
        assert self.spot.metrics.total_requests == 0

    @patch('requests.get')
    def test_analyze_success(self, mock_get):
        """Test successful analysis."""
        # Mock SSE response
        sse_data = b"""data: info depth 15 multipv 1 score cp 25 pv e2e4 e7e5
data: info depth 15 multipv 2 score cp 15 pv d2d4 d7d5
data: info depth 15 multipv 3 score mate 3 pv f2f4 e7e5
"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = sse_data.split(b'\n')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Test analyze
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = self.spot.analyze(fen, depth=15, multipv=3)

        # Verify result
        assert isinstance(result, EngineResult)
        assert len(result.lines) == 3

        # Check first line
        assert result.lines[0].multipv == 1
        assert result.lines[0].score == 25
        assert result.lines[0].pv == ['e2e4', 'e7e5']

        # Check second line
        assert result.lines[1].multipv == 2
        assert result.lines[1].score == 15

        # Check third line (mate score)
        assert result.lines[2].multipv == 3
        assert result.lines[2].score == "mate3"

        # Verify metrics updated
        assert self.spot.metrics.total_requests == 1
        assert self.spot.metrics.failure_count == 0
        assert self.spot.metrics.success_rate == 1.0
        assert self.spot.metrics.status == SpotStatus.HEALTHY
        assert self.spot.metrics.avg_latency_ms > 0
        assert self.spot.metrics.last_healthy_at is not None

        # Verify request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "http://localhost:8001/analyze/stream"
        assert call_args[1]['params']['fen'] == fen
        assert call_args[1]['params']['depth'] == 15
        assert call_args[1]['params']['multipv'] == 3
        assert call_args[1]['timeout'] == 30

    @patch('requests.get')
    def test_analyze_timeout(self, mock_get):
        """Test analysis timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            self.spot.analyze(fen)
            assert False, "Expected ChessEngineTimeoutError"
        except ChessEngineTimeoutError as e:
            assert str(self.spot.timeout) in str(e) or "30" in str(e)

        # Verify metrics updated
        assert self.spot.metrics.total_requests == 1
        assert self.spot.metrics.failure_count == 1
        assert self.spot.metrics.success_rate == 0.0

    @patch('requests.get')
    def test_analyze_connection_error(self, mock_get):
        """Test analysis connection error."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            self.spot.analyze(fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError as e:
            assert "test-spot" in str(e)

        # Verify metrics updated
        assert self.spot.metrics.total_requests == 1
        assert self.spot.metrics.failure_count == 1

    @patch('requests.get')
    def test_analyze_http_error(self, mock_get):
        """Test analysis HTTP error (4xx/5xx)."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            self.spot.analyze(fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError:
            pass

        # Verify metrics updated
        assert self.spot.metrics.failure_count == 1

    @patch('requests.get')
    def test_analyze_empty_response(self, mock_get):
        """Test analysis with empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            self.spot.analyze(fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError as e:
            assert "No analysis data" in str(e)

        # Verify metrics updated
        assert self.spot.metrics.failure_count == 1

    @patch('requests.get')
    def test_analyze_malformed_response(self, mock_get):
        """Test analysis with malformed response."""
        sse_data = b"""data: info depth 15 multipv invalid_data
data: garbage
"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = sse_data.split(b'\n')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            self.spot.analyze(fen)
            assert False, "Expected ChessEngineError"
        except ChessEngineError:
            pass

    @patch('requests.get')
    def test_analyze_multiple_successes(self, mock_get):
        """Test multiple successful analyses update metrics correctly."""
        # Mock SSE response
        sse_data = b"data: info depth 15 multipv 1 score cp 25 pv e2e4\n"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = sse_data.split(b'\n')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        # Make 3 successful requests
        for i in range(3):
            result = self.spot.analyze(fen)
            assert len(result.lines) > 0

        # Verify metrics
        assert self.spot.metrics.total_requests == 3
        assert self.spot.metrics.failure_count == 0
        assert self.spot.metrics.success_rate == 1.0
        assert self.spot.metrics.status == SpotStatus.HEALTHY

    @patch('requests.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.spot.health_check()

        assert result is True
        mock_get.assert_called_once_with("http://localhost:8001/health", timeout=5)

    @patch('requests.get')
    def test_health_check_failure_status(self, mock_get):
        """Test health check with non-200 status."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        result = self.spot.health_check()

        assert result is False

    @patch('requests.get')
    def test_health_check_connection_error(self, mock_get):
        """Test health check with connection error."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        result = self.spot.health_check()

        assert result is False

    @patch('requests.get')
    def test_health_check_timeout(self, mock_get):
        """Test health check with timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        result = self.spot.health_check()

        assert result is False

    def test_custom_timeout(self):
        """Test spot with custom timeout."""
        spot = EngineSpot(self.config, timeout=10)
        assert spot.timeout == 10


if __name__ == "__main__":
    # Simple test runner
    import inspect

    test_class = TestEngineSpot()
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
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
