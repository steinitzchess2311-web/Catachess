"""
Accurate Knight-Bishop Exchange tag detector.

Detects when a player exchanges a minor piece (knight or bishop) for an
opponent's minor piece with minimal evaluation loss.

Conditions:
- Move is a minor piece (N/B) capturing opponent's minor piece (N/B)
- Evaluation delta < 10cp (minimal loss)

Evidence:
- captured_piece: The piece that was captured
- capturing_piece: The piece that made the capture
- delta_eval_cp: Evaluation change in centipawns
- threshold: The threshold for accurate exchange
"""
import chess
from ...models import TagContext, TagEvidence


ACCURATE_THRESHOLD_CP = 10  # < 10cp loss


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect accurate knight-bishop exchange.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    board = ctx.board
    move = ctx.played_move
    delta_eval_cp = int(ctx.delta_eval * 100)

    # Get pieces
    moving_piece = board.piece_at(move.from_square)
    captured_piece = board.piece_at(move.to_square)

    # Store evidence
    evidence["delta_eval_cp"] = delta_eval_cp
    evidence["threshold_cp"] = ACCURATE_THRESHOLD_CP
    evidence["from_square"] = chess.square_name(move.from_square)
    evidence["to_square"] = chess.square_name(move.to_square)

    if moving_piece:
        evidence["capturing_piece"] = chess.piece_name(moving_piece.piece_type)
    if captured_piece:
        evidence["captured_piece"] = chess.piece_name(captured_piece.piece_type)

    # Gate 1: Is capture move
    if captured_piece:
        gates_passed.append("is_capture")
    else:
        gates_failed.append("is_capture")
        return TagEvidence(
            tag="accurate_knight_bishop_exchange",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Gate 2: Capturing piece is minor piece
    if moving_piece and moving_piece.piece_type in (chess.KNIGHT, chess.BISHOP):
        gates_passed.append("capturing_minor_piece")
    else:
        gates_failed.append("capturing_minor_piece")

    # Gate 3: Captured piece is minor piece
    if captured_piece.piece_type in (chess.KNIGHT, chess.BISHOP):
        gates_passed.append("captured_minor_piece")
    else:
        gates_failed.append("captured_minor_piece")

    # Gate 4: Evaluation loss is minimal (< 10cp)
    if delta_eval_cp > -ACCURATE_THRESHOLD_CP:
        gates_passed.append("minimal_eval_loss")
    else:
        gates_failed.append("minimal_eval_loss")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Confidence based on how good the exchange was
    if fired:
        # Better (less negative) eval = higher confidence
        if delta_eval_cp >= 0:
            confidence = 1.0  # Actually gained evaluation
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


__all__ = ["detect"]
