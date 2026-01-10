"""
Tests for shared modules (metrics, phase, contact, tactical_weight, control_helpers).
"""
import chess
import pytest
from backend.modules.tagger_core.legacy.shared import (
    contact,
    phase,
    metrics,
    tactical_weight,
    control_helpers,
)


class TestContactModule:
    """Tests for contact.py module."""

    def test_contact_profile_starting_position(self):
        """Test contact ratio for starting position."""
        board = chess.Board()
        ratio, total, captures, checks = contact.contact_profile(board)

        assert 0.0 <= ratio <= 1.0
        assert total == 20  # Starting position has 20 legal moves
        assert captures == 0  # No captures possible
        assert checks == 0  # No checks possible

    def test_contact_ratio_simplified(self):
        """Test simplified contact_ratio function."""
        board = chess.Board()
        ratio = contact.contact_ratio(board)

        assert ratio == 0.0  # Starting position has no contact moves

    def test_contact_profile_tactical_position(self):
        """Test contact profile in a tactical position."""
        # Position with multiple captures available
        board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
        ratio, total, captures, checks = contact.contact_profile(board)

        assert ratio > 0.0  # Should have some contact moves
        assert captures > 0  # Should have capture opportunities


class TestPhaseModule:
    """Tests for phase.py module."""

    def test_estimate_phase_ratio_starting_position(self):
        """Test phase ratio for starting position."""
        board = chess.Board()
        ratio = phase.estimate_phase_ratio(board)

        assert 0.9 <= ratio <= 1.0  # Opening should be close to 1.0

    def test_estimate_phase_ratio_endgame(self):
        """Test phase ratio for endgame position."""
        # K+P vs K endgame
        board = chess.Board("8/8/8/8/4k3/8/4P3/4K3 w - - 0 1")
        ratio = phase.estimate_phase_ratio(board)

        assert 0.0 <= ratio <= 0.2  # Endgame should be close to 0.0

    def test_get_phase_bucket(self):
        """Test phase bucket assignment."""
        assert phase.get_phase_bucket(0.0) == "endgame"
        assert phase.get_phase_bucket(0.2) == "endgame"
        assert phase.get_phase_bucket(0.5) == "middlegame"
        assert phase.get_phase_bucket(0.9) == "opening"
        assert phase.get_phase_bucket(1.0) == "opening"


class TestMetricsModule:
    """Tests for metrics.py module."""

    def test_evaluation_and_metrics_returns_correct_keys(self):
        """Test that metrics computation returns all expected keys."""
        board = chess.Board()
        m, opp_m, eval_dict = metrics.evaluation_and_metrics(board, chess.WHITE)

        # Check all style component keys are present
        for key in metrics.STYLE_COMPONENT_KEYS:
            assert key in m
            assert key in opp_m

    def test_metrics_delta_computation(self):
        """Test metrics delta computation."""
        before = {
            "mobility": 0.5,
            "center_control": 0.3,
            "king_safety": 0.2,
            "structure": 0.1,
            "tactics": 0.0,
        }
        after = {
            "mobility": 0.6,
            "center_control": 0.4,
            "king_safety": 0.2,
            "structure": 0.0,
            "tactics": 0.1,
        }

        delta = metrics.metrics_delta(before, after)

        assert delta["mobility"] == pytest.approx(0.1, abs=0.01)
        assert delta["center_control"] == pytest.approx(0.1, abs=0.01)
        assert delta["king_safety"] == pytest.approx(0.0, abs=0.01)
        assert delta["structure"] == pytest.approx(-0.1, abs=0.01)
        assert delta["tactics"] == pytest.approx(0.1, abs=0.01)


class TestTacticalWeightModule:
    """Tests for tactical_weight.py module."""

    def test_compute_tactical_weight_quiet_position(self):
        """Test tactical weight for quiet position."""
        weight = tactical_weight.compute_tactical_weight(
            delta_eval_cp=0,
            delta_tactics=0.0,
            delta_structure=0.0,
            depth_jump_cp=0,
            deepening_gain_cp=0,
            score_gap_cp=0,
            contact_ratio=0.0,
            phase_ratio=1.0,
            best_is_forcing=False,
            played_is_forcing=False,
            mate_threat=False,
        )

        assert 0.0 <= weight <= 1.0
        assert weight < 0.5  # Should be low for quiet position

    def test_compute_tactical_weight_tactical_position(self):
        """Test tactical weight for tactical position."""
        weight = tactical_weight.compute_tactical_weight(
            delta_eval_cp=-200,  # Large eval swing
            delta_tactics=0.5,   # Tactics change
            delta_structure=-0.1,
            depth_jump_cp=150,
            deepening_gain_cp=100,
            score_gap_cp=300,
            contact_ratio=0.8,   # High contact
            phase_ratio=0.7,
            best_is_forcing=True,
            played_is_forcing=True,
            mate_threat=True,
        )

        assert 0.0 <= weight <= 1.0
        assert weight > 0.5  # Should be high for tactical position


class TestControlHelpersModule:
    """Tests for control_helpers.py module."""

    def test_contact_stats(self):
        """Test contact_stats function."""
        board = chess.Board()
        stats = control_helpers.contact_stats(board, chess.WHITE)

        assert "ratio" in stats
        assert "total" in stats
        assert "contact" in stats
        assert "captures" in stats
        assert "checks" in stats

    def test_control_tension_threshold(self):
        """Test phase-dependent tension thresholds."""
        opening_threshold = control_helpers.control_tension_threshold("opening")
        mid_threshold = control_helpers.control_tension_threshold("middlegame")
        end_threshold = control_helpers.control_tension_threshold("endgame")

        # All should be negative (tension decrease required)
        assert opening_threshold < 0
        assert mid_threshold < 0
        assert end_threshold < 0

    def test_count_legal_moves(self):
        """Test counting legal moves for a color."""
        board = chess.Board()
        white_moves = control_helpers.count_legal_moves_for(board, chess.WHITE)

        assert white_moves == 20  # Starting position

    def test_active_piece_count(self):
        """Test active piece counting."""
        board = chess.Board()
        count = control_helpers.active_piece_count(board)

        # Starting position: 4 knights + 4 bishops + 4 rooks + 2 queens = 14
        assert count == 14

    def test_active_piece_count_for_color(self):
        """Test active piece counting for specific color."""
        board = chess.Board()
        white_count = control_helpers.active_piece_count_for(board, chess.WHITE)
        black_count = control_helpers.active_piece_count_for(board, chess.BLACK)

        assert white_count == 7  # 2N + 2B + 2R + 1Q
        assert black_count == 7
