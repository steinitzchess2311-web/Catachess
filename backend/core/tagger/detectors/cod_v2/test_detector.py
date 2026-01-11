"""
Unit tests for CoD v2 detector.
Basic golden tests for each subtype.
"""
import chess
from .detector import ControlOverDynamicsV2Detector
from .models import CoDContext, CoDMetrics
from .result import CoDSubtype


def test_prophylaxis_detection():
    """Test prophylaxis subtype detection."""
    metrics = CoDMetrics(
        preventive_score=0.30,
        threat_delta=0.25,
        opp_mobility_drop=0.20,
    )

    ctx = CoDContext(
        board=chess.Board(),
        played_move=chess.Move.from_uci("e2e4"),
        actor=chess.WHITE,
        metrics=metrics,
    )

    detector = ControlOverDynamicsV2Detector()
    result = detector.detect(ctx)

    assert result.detected
    assert result.subtype == CoDSubtype.PROPHYLAXIS
    assert result.confidence > 0


def test_piece_control_detection():
    """Test piece control subtype detection."""
    metrics = CoDMetrics(
        opp_mobility_drop=0.20,
        volatility_drop_cp=100.0,
        self_mobility_change=0.05,
    )

    ctx = CoDContext(
        board=chess.Board(),
        played_move=chess.Move.from_uci("g1f3"),
        actor=chess.WHITE,
        metrics=metrics,
    )

    detector = ControlOverDynamicsV2Detector()
    result = detector.detect(ctx)

    assert result.detected
    assert result.subtype == CoDSubtype.PIECE_CONTROL


def test_pawn_control_detection():
    """Test pawn control subtype detection."""
    metrics = CoDMetrics(
        blockade_established=True,
        opp_passed_push_drop=0.15,
        structure_gain=0.20,
    )

    ctx = CoDContext(
        board=chess.Board(),
        played_move=chess.Move.from_uci("d2d4"),
        actor=chess.WHITE,
        metrics=metrics,
    )

    detector = ControlOverDynamicsV2Detector()
    result = detector.detect(ctx)

    assert result.detected
    assert result.subtype == CoDSubtype.PAWN_CONTROL


def test_simplification_detection():
    """Test simplification subtype detection."""
    metrics = CoDMetrics(
        exchange_count=1,
        total_active_drop=4,
        opp_active_drop=2,
        own_active_drop=2,
    )

    ctx = CoDContext(
        board=chess.Board(),
        played_move=chess.Move.from_uci("d1d8"),
        actor=chess.WHITE,
        metrics=metrics,
        eval_drop_cp=-20,
    )

    detector = ControlOverDynamicsV2Detector()
    result = detector.detect(ctx)

    assert result.detected
    assert result.subtype == CoDSubtype.SIMPLIFICATION


def test_cooldown_enforcement():
    """Test cooldown prevents detection."""
    metrics = CoDMetrics(
        preventive_score=0.30,
        threat_delta=0.25,
        opp_mobility_drop=0.20,
    )

    ctx = CoDContext(
        board=chess.Board(),
        played_move=chess.Move.from_uci("e2e4"),
        actor=chess.WHITE,
        metrics=metrics,
        current_ply=10,
        last_cod_ply=8,  # Too recent (2 plies ago)
    )

    detector = ControlOverDynamicsV2Detector()
    result = detector.detect(ctx)

    assert not result.detected
    assert "cooldown" in result.gates_failed


if __name__ == "__main__":
    # Run tests
    test_prophylaxis_detection()
    print("✓ test_prophylaxis_detection")

    test_piece_control_detection()
    print("✓ test_piece_control_detection")

    test_pawn_control_detection()
    print("✓ test_pawn_control_detection")

    test_simplification_detection()
    print("✓ test_simplification_detection")

    test_cooldown_enforcement()
    print("✓ test_cooldown_enforcement")

    print("\nAll CoD v2 tests passed!")
