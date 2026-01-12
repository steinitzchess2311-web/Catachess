"""
Opening Central Pawn Move tag detector.

Detects when a player pushes a central pawn (d4, e4, d5, e5) during the
opening phase of the game.

Conditions:
- Move is a pawn move
- Destination is d4, e4, d5, or e5
- Fullmove number <= 15
- At least 28 pieces on board (minimal early trades allowed)

Evidence:
- destination_square: The square the pawn moved to
- fullmove_number: Move number in the game
- piece_count: Number of pieces on board
"""
import chess
from core.tagger.models import TagContext, TagEvidence


# Constants from legacy
OPENING_PAWN_FULLMOVE_CUTOFF = 15
CENTRAL_PAWN_OPENING_TARGETS = {chess.D4, chess.E4, chess.D5, chess.E5}
MIN_PIECES_FOR_OPENING = 28


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect opening central pawn move.

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
    piece = board.piece_at(move.from_square)

    # Store evidence
    evidence["from_square"] = chess.square_name(move.from_square)
    evidence["to_square"] = chess.square_name(move.to_square)
    evidence["fullmove_number"] = board.fullmove_number
    evidence["piece_count"] = len(board.piece_map())

    # Gate 1: Is pawn move
    if piece and piece.piece_type == chess.PAWN:
        gates_passed.append("is_pawn_move")
    else:
        gates_failed.append("is_pawn_move")
        return TagEvidence(
            tag="opening_central_pawn_move",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Gate 2: Destination is central square
    dest = move.to_square
    if dest in CENTRAL_PAWN_OPENING_TARGETS:
        gates_passed.append("central_square")
        evidence["destination_square"] = chess.square_name(dest)
    else:
        gates_failed.append("central_square")

    # Gate 3: Within opening phase
    if board.fullmove_number <= OPENING_PAWN_FULLMOVE_CUTOFF:
        gates_passed.append("opening_phase")
    else:
        gates_failed.append("opening_phase")

    # Gate 4: Sufficient pieces on board
    if len(board.piece_map()) >= MIN_PIECES_FOR_OPENING:
        gates_passed.append("sufficient_pieces")
    else:
        gates_failed.append("sufficient_pieces")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Confidence is high if fired (simple deterministic check)
    confidence = 1.0 if fired else 0.0

    return TagEvidence(
        tag="opening_central_pawn_move",
        fired=fired,
        confidence=confidence,
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
