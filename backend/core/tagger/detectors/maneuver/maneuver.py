"""Maneuver tag detectors - 5 detectors in 1 file."""
import chess
from ...models import TagContext, TagEvidence
from ...detectors.helpers.maneuver import compute_maneuver_score

def detect_constructive_maneuver(ctx: TagContext) -> TagEvidence:
    """Constructive maneuver."""
    gates_passed, gates_failed, evidence = [], [], {}
    piece = ctx.board.piece_at(ctx.played_move.from_square)
    is_light = piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP)
    maneuver_score = compute_maneuver_score(ctx)
    evidence.update({"is_light_piece": is_light, "maneuver_score": maneuver_score})
    
    if is_light and maneuver_score > 0.3:
        gates_passed.append("constructive")
        fired, confidence = True, 0.7 + min(0.3, maneuver_score * 0.5)
    else:
        gates_failed.append("constructive")
        fired, confidence = False, 0.0
    
    return TagEvidence("constructive_maneuver", fired, min(1.0, confidence), evidence, gates_passed, gates_failed)

def detect_constructive_maneuver_prepare(ctx: TagContext) -> TagEvidence:
    """Constructive maneuver prepare."""
    gates_passed, gates_failed, evidence = [], [], {}
    piece = ctx.board.piece_at(ctx.played_move.from_square)
    is_light = piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP)
    maneuver_score = compute_maneuver_score(ctx)
    evidence.update({"is_light_piece": is_light, "maneuver_score": maneuver_score})
    
    if is_light and 0.1 < maneuver_score <= 0.3:
        gates_passed.append("prepare")
        fired, confidence = True, 0.6
    else:
        gates_failed.append("prepare")
        fired, confidence = False, 0.0
    
    return TagEvidence("constructive_maneuver_prepare", fired, confidence, evidence, gates_passed, gates_failed)

def detect_neutral_maneuver(ctx: TagContext) -> TagEvidence:
    """Neutral maneuver."""
    gates_passed, gates_failed, evidence = [], [], {}
    piece = ctx.board.piece_at(ctx.played_move.from_square)
    is_light = piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP)
    maneuver_score = compute_maneuver_score(ctx)
    evidence.update({"is_light_piece": is_light, "maneuver_score": maneuver_score})
    
    if is_light and -0.1 <= maneuver_score <= 0.1:
        gates_passed.append("neutral")
        fired, confidence = True, 0.6
    else:
        gates_failed.append("neutral")
        fired, confidence = False, 0.0
    
    return TagEvidence("neutral_maneuver", fired, confidence, evidence, gates_passed, gates_failed)

def detect_misplaced_maneuver(ctx: TagContext) -> TagEvidence:
    """Misplaced maneuver."""
    gates_passed, gates_failed, evidence = [], [], {}
    piece = ctx.board.piece_at(ctx.played_move.from_square)
    is_light = piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP)
    maneuver_score = compute_maneuver_score(ctx)
    evidence.update({"is_light_piece": is_light, "maneuver_score": maneuver_score})
    
    if is_light and maneuver_score < -0.2:
        gates_passed.append("misplaced")
        fired, confidence = True, 0.7
    else:
        gates_failed.append("misplaced")
        fired, confidence = False, 0.0
    
    return TagEvidence("misplaced_maneuver", fired, confidence, evidence, gates_passed, gates_failed)

def detect_maneuver_opening(ctx: TagContext) -> TagEvidence:
    """Maneuver in opening."""
    gates_passed, gates_failed, evidence = [], [], {}
    piece = ctx.board.piece_at(ctx.played_move.from_square)
    is_light = piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP)
    is_opening = ctx.move_number <= 15
    evidence.update({"is_light_piece": is_light, "is_opening": is_opening})
    
    if is_light and is_opening:
        gates_passed.append("opening_maneuver")
        fired, confidence = True, 0.7
    else:
        gates_failed.append("opening_maneuver")
        fired, confidence = False, 0.0
    
    return TagEvidence("maneuver_opening", fired, confidence, evidence, gates_passed, gates_failed)

__all__ = ["detect_constructive_maneuver", "detect_constructive_maneuver_prepare", "detect_neutral_maneuver", "detect_misplaced_maneuver", "detect_maneuver_opening"]
