"""
Knight-Bishop Exchange tag detectors.

This module contains three detectors for knight-bishop exchanges with different quality levels:
- accurate: eval loss < 10cp
- inaccurate: eval loss 10-30cp
- bad: eval loss > 30cp

All three share similar logic but differ in thresholds.
"""
import chess
from ...models import TagContext, TagEvidence


# Thresholds in centipawns
ACCURATE_THRESHOLD_CP = 10
INACCURATE_THRESHOLD_LOW_CP = 10
INACCURATE_THRESHOLD_HIGH_CP = 30
BAD_THRESHOLD_CP = 30


def _is_minor_piece_exchange(ctx: TagContext) -> tuple[bool, dict]:
    """
    Check if move is a minor piece exchange.
    
    Returns:
        (is_exchange, evidence_dict)
    """
    board = ctx.board
    move = ctx.played_move
    
    moving_piece = board.piece_at(move.from_square)
    captured_piece = board.piece_at(move.to_square)
    
    evidence = {
        "delta_eval_cp": int(ctx.delta_eval * 100),
        "from_square": chess.square_name(move.from_square),
        "to_square": chess.square_name(move.to_square),
    }
    
    if moving_piece:
        evidence["capturing_piece"] = chess.piece_name(moving_piece.piece_type)
    if captured_piece:
        evidence["captured_piece"] = chess.piece_name(captured_piece.piece_type)
    
    # Check if both pieces are minor pieces
    is_exchange = (
        captured_piece is not None and
        moving_piece is not None and
        moving_piece.piece_type in (chess.KNIGHT, chess.BISHOP) and
        captured_piece.piece_type in (chess.KNIGHT, chess.BISHOP)
    )
    
    return is_exchange, evidence


def detect_accurate_knight_bishop_exchange(ctx: TagContext) -> TagEvidence:
    """
    Detect accurate knight-bishop exchange (eval loss < 10cp).
    """
    gates_passed = []
    gates_failed = []
    
    is_exchange, evidence = _is_minor_piece_exchange(ctx)
    delta_eval_cp = evidence["delta_eval_cp"]
    evidence["threshold_cp"] = ACCURATE_THRESHOLD_CP
    
    # Gate 1: Is minor piece exchange
    if is_exchange:
        gates_passed.append("is_minor_exchange")
    else:
        gates_failed.append("is_minor_exchange")
        return TagEvidence(
            tag="accurate_knight_bishop_exchange",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )
    
    # Gate 2: Eval loss is minimal (< 10cp)
    if delta_eval_cp > -ACCURATE_THRESHOLD_CP:
        gates_passed.append("minimal_eval_loss")
    else:
        gates_failed.append("minimal_eval_loss")
    
    fired = len(gates_passed) == 2
    
    # Confidence based on eval loss
    if fired:
        if delta_eval_cp >= 0:
            confidence = 1.0
        else:
            confidence = 0.7 + (0.3 * (ACCURATE_THRESHOLD_CP + delta_eval_cp) / ACCURATE_THRESHOLD_CP)
    else:
        confidence = 0.0
    
    return TagEvidence(
        tag="accurate_knight_bishop_exchange",
        fired=fired,
        confidence=min(1.0, max(0.0, confidence)),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


def detect_inaccurate_knight_bishop_exchange(ctx: TagContext) -> TagEvidence:
    """
    Detect inaccurate knight-bishop exchange (eval loss 10-30cp).
    """
    gates_passed = []
    gates_failed = []
    
    is_exchange, evidence = _is_minor_piece_exchange(ctx)
    delta_eval_cp = evidence["delta_eval_cp"]
    evidence["threshold_low_cp"] = INACCURATE_THRESHOLD_LOW_CP
    evidence["threshold_high_cp"] = INACCURATE_THRESHOLD_HIGH_CP
    
    # Gate 1: Is minor piece exchange
    if is_exchange:
        gates_passed.append("is_minor_exchange")
    else:
        gates_failed.append("is_minor_exchange")
        return TagEvidence(
            tag="inaccurate_knight_bishop_exchange",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )
    
    # Gate 2: Eval loss in range [10, 30]cp
    if -INACCURATE_THRESHOLD_HIGH_CP <= delta_eval_cp <= -INACCURATE_THRESHOLD_LOW_CP:
        gates_passed.append("eval_loss_in_range")
    else:
        gates_failed.append("eval_loss_in_range")
    
    fired = len(gates_passed) == 2
    
    # Confidence based on eval loss (middle range)
    if fired:
        # Closer to 10cp = higher confidence
        range_size = INACCURATE_THRESHOLD_HIGH_CP - INACCURATE_THRESHOLD_LOW_CP
        position_in_range = abs(delta_eval_cp + INACCURATE_THRESHOLD_LOW_CP)
        confidence = 0.8 - (0.3 * position_in_range / range_size)
    else:
        confidence = 0.0
    
    return TagEvidence(
        tag="inaccurate_knight_bishop_exchange",
        fired=fired,
        confidence=min(1.0, max(0.0, confidence)),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


def detect_bad_knight_bishop_exchange(ctx: TagContext) -> TagEvidence:
    """
    Detect bad knight-bishop exchange (eval loss > 30cp).
    """
    gates_passed = []
    gates_failed = []
    
    is_exchange, evidence = _is_minor_piece_exchange(ctx)
    delta_eval_cp = evidence["delta_eval_cp"]
    evidence["threshold_cp"] = BAD_THRESHOLD_CP
    
    # Gate 1: Is minor piece exchange
    if is_exchange:
        gates_passed.append("is_minor_exchange")
    else:
        gates_failed.append("is_minor_exchange")
        return TagEvidence(
            tag="bad_knight_bishop_exchange",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )
    
    # Gate 2: Eval loss is significant (> 30cp)
    if delta_eval_cp < -BAD_THRESHOLD_CP:
        gates_passed.append("significant_eval_loss")
    else:
        gates_failed.append("significant_eval_loss")
    
    fired = len(gates_passed) == 2
    
    # Confidence based on eval loss (worse = higher confidence)
    if fired:
        # More negative eval = higher confidence
        confidence = 0.7 + min(0.3, abs(delta_eval_cp + BAD_THRESHOLD_CP) / 100.0)
    else:
        confidence = 0.0
    
    return TagEvidence(
        tag="bad_knight_bishop_exchange",
        fired=fired,
        confidence=min(1.0, max(0.0, confidence)),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = [
    "detect_accurate_knight_bishop_exchange",
    "detect_inaccurate_knight_bishop_exchange",
    "detect_bad_knight_bishop_exchange",
]
