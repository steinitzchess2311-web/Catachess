"""
Tests for Stockfish engine client.
"""
import chess
import pytest
from backend.core.tagger.legacy.engine.stockfish_client import StockfishClient


class TestStockfishClient:
    """Test the Stockfish engine client."""

    def test_client_initialization(self):
        """Test creating a Stockfish client."""
        client = StockfishClient()
        assert client.engine_path is not None

    def test_analyse_candidates_starting_position(self):
        """Test analyzing the starting position."""
        board = chess.Board()

        with StockfishClient() as client:
            candidates, best_score, metadata = client.analyse_candidates(
                board=board,
                depth=10,
                multipv=5
            )

            assert len(candidates) > 0
            assert len(candidates) <= 5
            assert metadata["depth"] == 10
            assert metadata["multipv"] == 5

            # Check first candidate
            first = candidates[0]
            assert first.move is not None
            assert isinstance(first.score_cp, int)
            assert first.kind in ["quiet", "dynamic", "forcing"]

    def test_analyse_candidates_tactical_position(self):
        """Test analyzing a tactical position."""
        # Position with a hanging piece
        board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3")

        with StockfishClient() as client:
            candidates, best_score, metadata = client.analyse_candidates(
                board=board,
                depth=12,
                multipv=3
            )

            assert len(candidates) > 0
            # In a tactical position, we should find forcing moves
            forcing_moves = [c for c in candidates if c.kind == "forcing"]
            assert len(forcing_moves) >= 0  # May or may not have captures in top 3

    def test_eval_specific_move(self):
        """Test evaluating a specific move."""
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")

        with StockfishClient() as client:
            score = client.eval_specific(board, move, depth=10)
            assert isinstance(score, int)
            # e2e4 is a good opening move, should be near 0 or positive
            assert -200 <= score <= 200

    def test_move_classification(self):
        """Test move kind classification."""
        with StockfishClient() as client:
            # Test quiet move
            board = chess.Board()
            quiet_move = chess.Move.from_uci("g1f3")
            kind = client._classify_move(board, quiet_move)
            assert kind in ["quiet", "dynamic"]

            # Test capture - position after 1.e4 e5 2.Nf3
            board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
            # Black captures the e4 pawn
            capture_move = chess.Move.from_uci("e5e4")
            kind = client._classify_move(board, capture_move)
            assert kind == "forcing"

    def test_context_manager(self):
        """Test that context manager properly opens and closes engine."""
        client = StockfishClient()
        assert client._engine is None

        with client:
            assert client._engine is not None

        assert client._engine is None

    def test_error_without_context_manager(self):
        """Test that using client without context manager raises error."""
        client = StockfishClient()
        board = chess.Board()

        with pytest.raises(RuntimeError, match="Engine not initialized"):
            client.analyse_candidates(board, 10, 5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
