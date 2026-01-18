"""
Test the first_choice tag detector.
"""
import chess
from backend.core.tagger.models import TagContext, Candidate
from backend.core.tagger.legacy.tags.first_choice import detect


class TestFirstChoiceDetector:
    """Test first_choice tag detection."""

    def test_fires_when_played_is_best(self):
        """Test that first_choice fires when played move is best."""
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")

        ctx = TagContext(
            board=board,
            board_before=board,
            fen=board.fen(),
            played_move=move,
            actor=chess.WHITE,
            is_capture=False,
            is_check=False,
            move_number=1,
            candidates=[Candidate(move, 20, "dynamic")],
            best_move=move,  # Same as played
            played_kind="dynamic",
            best_kind="dynamic",
            eval_before_cp=15,
            eval_played_cp=20,
            eval_best_cp=20,
            eval_before=0.15,
            eval_played=0.20,
            eval_best=0.20,
            delta_eval=0.05,
            metrics_before={},
            metrics_played={},
            metrics_best={},
            component_deltas={},
            opp_metrics_before={},
            opp_metrics_played={},
            opp_metrics_best={},
            opp_component_deltas={},
            phase_ratio=0.0,
            phase_bucket="opening",
            contact_ratio_before=0.1,
            contact_ratio_played=0.1,
            contact_ratio_best=0.1,
            tactical_weight=0.2,
            coverage_delta=0,
            has_dynamic_in_band=True,
            analysis_meta={},
            engine_depth=14,
            engine_multipv=6,
        )

        evidence = detect(ctx)

        assert evidence.tag == "first_choice"
        assert evidence.fired is True
        assert evidence.confidence == 1.0
        assert "played_is_best" in evidence.gates_passed
        assert len(evidence.gates_failed) == 0

    def test_does_not_fire_when_played_differs(self):
        """Test that first_choice doesn't fire for non-best moves."""
        board = chess.Board()
        played_move = chess.Move.from_uci("d2d4")
        best_move = chess.Move.from_uci("e2e4")

        ctx = TagContext(
            board=board,
            board_before=board,
            fen=board.fen(),
            played_move=played_move,
            actor=chess.WHITE,
            is_capture=False,
            is_check=False,
            move_number=1,
            candidates=[
                Candidate(best_move, 25, "dynamic"),
                Candidate(played_move, -50, "quiet"),
            ],
            best_move=best_move,  # Different from played
            played_kind="quiet",
            best_kind="dynamic",
            eval_before_cp=15,
            eval_played_cp=-85,
            eval_best_cp=25,
            eval_before=0.15,
            eval_played=-0.85,
            eval_best=0.25,
            delta_eval=-1.00,  # Large delta (100cp), not first choice
            metrics_before={},
            metrics_played={},
            metrics_best={},
            component_deltas={},
            opp_metrics_before={},
            opp_metrics_played={},
            opp_metrics_best={},
            opp_component_deltas={},
            phase_ratio=0.0,
            phase_bucket="opening",
            contact_ratio_before=0.1,
            contact_ratio_played=0.1,
            contact_ratio_best=0.1,
            tactical_weight=0.2,
            coverage_delta=0,
            has_dynamic_in_band=True,
            analysis_meta={},
            engine_depth=14,
            engine_multipv=6,
        )

        evidence = detect(ctx)

        assert evidence.tag == "first_choice"
        assert evidence.fired is False
        assert evidence.confidence == 0.0
        assert "played_is_best" in evidence.gates_failed
        assert "within_tactical_gap" in evidence.gates_failed

    def test_fires_within_tactical_gap(self):
        """Test that first_choice fires when within tactical threshold."""
        board = chess.Board()
        played_move = chess.Move.from_uci("d2d4")
        best_move = chess.Move.from_uci("e2e4")

        ctx = TagContext(
            board=board,
            board_before=board,
            fen=board.fen(),
            played_move=played_move,
            actor=chess.WHITE,
            is_capture=False,
            is_check=False,
            move_number=1,
            candidates=[
                Candidate(best_move, 25, "dynamic"),
                Candidate(played_move, 15, "quiet"),
            ],
            best_move=best_move,
            played_kind="quiet",
            best_kind="dynamic",
            eval_before_cp=15,
            eval_played_cp=15,
            eval_best_cp=25,
            eval_before=0.15,
            eval_played=0.15,
            eval_best=0.25,
            delta_eval=-0.10,  # Small delta (10cp), within 80cp threshold
            metrics_before={},
            metrics_played={},
            metrics_best={},
            component_deltas={},
            opp_metrics_before={},
            opp_metrics_played={},
            opp_metrics_best={},
            opp_component_deltas={},
            phase_ratio=0.0,
            phase_bucket="opening",
            contact_ratio_before=0.1,
            contact_ratio_played=0.1,
            contact_ratio_best=0.1,
            tactical_weight=0.2,
            coverage_delta=0,
            has_dynamic_in_band=True,
            analysis_meta={},
            engine_depth=14,
            engine_multipv=6,
        )

        evidence = detect(ctx)

        assert evidence.tag == "first_choice"
        assert evidence.fired is True
        assert evidence.confidence == 0.8
        assert "within_tactical_gap" in evidence.gates_passed
