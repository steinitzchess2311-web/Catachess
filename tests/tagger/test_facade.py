"""
Integration tests for the complete tagger system.
Tests the full flow from FEN + move to TagResult.
"""
import chess
import pytest
from backend.core.tagger.facade import tag_position


class TestFacadeSmokeTest:
    """Quick smoke tests to catch NameError-level wiring issues."""

    def test_tag_position_runs_without_nameerror(self):
        """
        Smoke test: Verify tag_position can execute without NameError.
        This catches typos in detector function names.
        """
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = "e2e4"

        # Should not raise NameError
        try:
            result = tag_position(
                engine_path=None,
                fen=fen,
                played_move_uci=move,
                depth=10,
                multipv=3,
            )
            # Basic sanity check
            assert result is not None
            assert result.played_move == move
        except NameError as e:
            pytest.fail(f"NameError in tag_position: {e}. Check for function name typos in facade.py")


class TestTaggerIntegration:
    """Integration tests for the tagger system."""

    def test_tag_starting_position_good_move(self):
        """Test tagging e2e4 in the starting position."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = "e2e4"

        result = tag_position(
            engine_path=None,  # Use default
            fen=fen,
            played_move_uci=move,
            depth=12,
            multipv=5,
        )

        # Basic checks
        assert result.played_move == move
        assert result.best_move in ["e2e4", "d2d4", "g1f3", "c2c4"]  # Common top moves
        assert result.played_kind in ["quiet", "dynamic"]

        # e2e4 is a good move, should be first choice or close
        assert result.first_choice or abs(result.delta_eval) < 0.5

        # Evaluation should be reasonable
        assert -0.5 <= result.eval_played <= 0.5

    def test_tag_starting_position_bad_move(self):
        """Test tagging a bad move in the starting position."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = "a2a4"  # Not terrible but not best

        result = tag_position(
            engine_path=None,
            fen=fen,
            played_move_uci=move,
            depth=12,
            multipv=5,
        )

        assert result.played_move == move
        # a2a4 is not first choice
        assert result.best_move != move or not result.first_choice

    def test_tag_tactical_position(self):
        """Test tagging in a tactical position."""
        # Position with hanging piece
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
        # Black should probably develop or push d5
        move = "g8f6"

        result = tag_position(
            engine_path=None,
            fen=fen,
            played_move_uci=move,
            depth=12,
            multipv=5,
        )

        assert result.played_move == move
        assert result.best_move is not None
        assert result.played_kind in ["quiet", "dynamic", "forcing"]

        # Evaluation should be tracked
        assert isinstance(result.eval_before, float)
        assert isinstance(result.eval_played, float)
        assert isinstance(result.delta_eval, float)

    def test_tag_endgame_position(self):
        """Test tagging in an endgame."""
        # Simple king and pawn endgame
        fen = "8/5k2/8/8/3K4/8/4P3/8 w - - 0 1"
        move = "e2e4"

        result = tag_position(
            engine_path=None,
            fen=fen,
            played_move_uci=move,
            depth=12,
            multipv=3,
        )

        assert result.played_move == move
        assert result.eval_played is not None

    def test_illegal_move_raises_error(self):
        """Test that illegal moves raise an error."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = "e2e5"  # Illegal - pawn can't jump

        with pytest.raises(ValueError, match="Illegal move"):
            tag_position(
                engine_path=None,
                fen=fen,
                played_move_uci=move,
                depth=12,
                multipv=5,
            )

    def test_result_has_all_required_fields(self):
        """Test that result has all required fields."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = "e2e4"

        result = tag_position(
            engine_path=None,
            fen=fen,
            played_move_uci=move,
            depth=10,
            multipv=5,
        )

        # Check all required fields exist
        assert hasattr(result, "played_move")
        assert hasattr(result, "best_move")
        assert hasattr(result, "eval_before")
        assert hasattr(result, "eval_played")
        assert hasattr(result, "eval_best")
        assert hasattr(result, "delta_eval")
        assert hasattr(result, "first_choice")
        assert hasattr(result, "mode")
        assert hasattr(result, "analysis_context")

        # Check tag fields exist (even if False)
        assert hasattr(result, "control_over_dynamics")
        assert hasattr(result, "tension_creation")
        assert hasattr(result, "prophylactic_move")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
