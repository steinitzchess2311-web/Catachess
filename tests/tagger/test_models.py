"""
Test suite for tagger core data models.
"""
import chess
import pytest
from backend.core.tagger.models import Candidate, TagContext, TagEvidence
from backend.core.tagger.tag_result import TagResult


class TestCandidate:
    """Test Candidate dataclass."""

    def test_candidate_creation(self):
        """Test creating a candidate move."""
        move = chess.Move.from_uci("e2e4")
        candidate = Candidate(move=move, score_cp=20, kind="quiet")

        assert candidate.move == move
        assert candidate.score_cp == 20
        assert candidate.kind == "quiet"

    def test_candidate_kinds(self):
        """Test different move kinds."""
        for kind in ["quiet", "dynamic", "forcing"]:
            candidate = Candidate(
                move=chess.Move.from_uci("e2e4"),
                score_cp=0,
                kind=kind
            )
            assert candidate.kind == kind


class TestTagEvidence:
    """Test TagEvidence dataclass."""

    def test_evidence_creation(self):
        """Test creating tag evidence."""
        evidence = TagEvidence(
            tag="tension_creation",
            fired=True,
            confidence=0.85,
            evidence={
                "mobility_delta": 0.42,
                "contact_ratio_change": 0.06,
                "threshold_met": True,
            },
            gates_passed=["eval_range", "mobility_threshold"],
            gates_failed=[],
        )

        assert evidence.tag == "tension_creation"
        assert evidence.fired is True
        assert evidence.confidence == 0.85
        assert len(evidence.evidence) == 3
        assert len(evidence.gates_passed) == 2
        assert len(evidence.gates_failed) == 0

    def test_failed_evidence(self):
        """Test evidence for a tag that didn't fire."""
        evidence = TagEvidence(
            tag="control_over_dynamics",
            fired=False,
            confidence=0.0,
            evidence={"mobility_drop": 0.05, "threshold": 0.10},
            gates_passed=[],
            gates_failed=["mobility_threshold", "eval_drop"],
        )

        assert evidence.fired is False
        assert len(evidence.gates_failed) == 2


class TestTagContext:
    """Test TagContext dataclass."""

    def test_context_creation(self):
        """Test creating a tag context."""
        board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        played_move = chess.Move.from_uci("e7e5")
        best_move = chess.Move.from_uci("e7e5")

        ctx = TagContext(
            board=board,
            fen=board.fen(),
            played_move=played_move,
            actor=chess.BLACK,
            candidates=[
                Candidate(best_move, 15, "quiet"),
                Candidate(chess.Move.from_uci("g8f6"), 10, "quiet"),
            ],
            best_move=best_move,
            played_kind="quiet",
            best_kind="quiet",
            eval_before_cp=20,
            eval_played_cp=15,
            eval_best_cp=15,
            eval_before=0.20,
            eval_played=0.15,
            eval_best=0.15,
            delta_eval=-0.05,
            metrics_before={"mobility": 0.5, "center_control": 0.3, "king_safety": 0.6, "structure": 0.5, "tactics": 0.2},
            metrics_played={"mobility": 0.6, "center_control": 0.4, "king_safety": 0.6, "structure": 0.5, "tactics": 0.2},
            metrics_best={"mobility": 0.6, "center_control": 0.4, "king_safety": 0.6, "structure": 0.5, "tactics": 0.2},
            component_deltas={"mobility": 0.1, "center_control": 0.1, "king_safety": 0.0, "structure": 0.0, "tactics": 0.0},
            opp_metrics_before={"mobility": 0.55, "center_control": 0.35, "king_safety": 0.65, "structure": 0.55, "tactics": 0.15},
            opp_metrics_played={"mobility": 0.50, "center_control": 0.30, "king_safety": 0.65, "structure": 0.55, "tactics": 0.15},
            opp_metrics_best={"mobility": 0.50, "center_control": 0.30, "king_safety": 0.65, "structure": 0.55, "tactics": 0.15},
            opp_component_deltas={"mobility": -0.05, "center_control": -0.05, "king_safety": 0.0, "structure": 0.0, "tactics": 0.0},
            phase_ratio=0.0,
            phase_bucket="opening",
            contact_ratio_before=0.10,
            contact_ratio_played=0.15,
            contact_ratio_best=0.15,
            tactical_weight=0.25,
            coverage_delta=5,
            has_dynamic_in_band=True,
            analysis_meta={},
            engine_depth=14,
            engine_multipv=6,
        )

        assert ctx.board == board
        assert ctx.played_move == played_move
        assert ctx.actor == chess.BLACK
        assert len(ctx.candidates) == 2
        assert ctx.phase_bucket == "opening"
        assert ctx.tactical_weight == 0.25


class TestTagResult:
    """Test TagResult dataclass."""

    def test_result_creation_minimal(self):
        """Test creating a minimal tag result."""
        result = TagResult(
            played_move="e2e4",
            played_kind="quiet",
            best_move="e2e4",
            best_kind="quiet",
            eval_before=0.15,
            eval_played=0.20,
            eval_best=0.20,
            delta_eval=0.05,
        )

        assert result.played_move == "e2e4"
        assert result.delta_eval == 0.05
        # Check defaults
        assert result.control_over_dynamics is False
        assert result.tension_creation is False
        assert result.prophylaxis_score == 0.0
        assert result.mode == "neutral"

    def test_result_with_tags(self):
        """Test creating a result with tags set."""
        result = TagResult(
            played_move="e2e4",
            played_kind="quiet",
            best_move="d2d4",
            best_kind="quiet",
            eval_before=0.15,
            eval_played=0.10,
            eval_best=0.15,
            delta_eval=-0.05,
            tension_creation=True,
            first_choice=False,
            tactical_weight=0.42,
            mode="neutral",
        )

        assert result.tension_creation is True
        assert result.first_choice is False
        assert result.tactical_weight == 0.42

    def test_result_with_metrics(self):
        """Test creating a result with full metrics."""
        metrics = {
            "mobility": 0.5,
            "center_control": 0.3,
            "king_safety": 0.6,
            "structure": 0.5,
            "tactics": 0.2,
        }

        result = TagResult(
            played_move="e2e4",
            played_kind="quiet",
            best_move="e2e4",
            best_kind="quiet",
            eval_before=0.15,
            eval_played=0.20,
            eval_best=0.20,
            delta_eval=0.05,
            metrics_before=metrics.copy(),
            metrics_played=metrics.copy(),
            metrics_best=metrics.copy(),
        )

        assert result.metrics_before == metrics
        assert result.metrics_played == metrics
        assert result.metrics_best == metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
