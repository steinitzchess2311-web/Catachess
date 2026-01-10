"""
Bad Knight-Bishop Exchange tag detector.

Detects when a player exchanges a minor piece (knight or bishop) for an
opponent's minor piece with significant evaluation loss.

Conditions:
- Move is a minor piece (N/B) capturing opponent's minor piece (N/B)
- Evaluation delta <= -30cp (significant loss)

Evidence:
- captured_piece: The piece that was captured
- capturing_piece: The piece that made the capture
- delta_eval_cp: Evaluation change in centipawns
- threshold: The threshold for bad exchange
"""
import chess
from ...models import TagContext, TagEvidence


BAD_THRESHOLD_CP = 30  # >= 30cp loss


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect bad knight-bishop exchange.

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
    evidence["threshold_cp"] = -BAD_THRESHOLD_CP
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
            tag="bad_knight_bishop_exchange",
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

    # Gate 4: Evaluation loss is significant (>= 30cp)
    if delta_eval_cp <= -BAD_THRESHOLD_CP:
        gates_passed.append("significant_eval_loss")
    else:
        gates_failed.append("significant_eval_loss")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Confidence based on how bad the exchange was
    if fired:
        # Worse (more negative) eval = higher confidence
        excess_loss = abs(delta_eval_cp) - BAD_THRESHOLD_CP
        confidence = 0.7 + min(0.3, excess_loss / 100.0)  # Up to 1.0 for very bad exchanges
    else:
        confidence = 0.0

    return TagEvidence(
        tag="bad_knight_bishop_exchange",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
