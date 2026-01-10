"""
Maneuver Opening tag detector.

Detects piece repositioning moves in the opening phase, which are common
as players develop pieces to optimal squares before the middlegame.

Conditions:
- Move is a maneuver candidate
- In opening phase (high phase_ratio)
- Move number <= 15
- Piece development/repositioning

Evidence:
- is_maneuver: Whether move is maneuver candidate
- phase_ratio: Game phase
- fullmove_number: Move number
- metrics: Position metric changes
"""
from ...models import TagContext, TagEvidence
from ..shared.maneuver_helpers import is_maneuver_candidate


OPENING_MOVE_CUTOFF = 15


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect opening maneuver.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    is_maneuver = is_maneuver_candidate(ctx)
    fullmove = ctx.board.fullmove_number

    mobility_change = ctx.component_deltas.get("mobility", 0.0)
    center_change = ctx.component_deltas.get("center_control", 0.0)

    # Store evidence
    evidence["is_maneuver_candidate"] = is_maneuver
    evidence["phase_ratio"] = ctx.phase_ratio
    evidence["phase_bucket"] = ctx.phase_bucket
    evidence["fullmove_number"] = fullmove
    evidence["mobility_change"] = mobility_change
    evidence["center_change"] = center_change

    # Gate 1: Is maneuver candidate
    if is_maneuver:
        gates_passed.append("is_maneuver")
    else:
        gates_failed.append("is_maneuver")
        return TagEvidence(
            tag="maneuver_opening",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Gate 2: In opening phase
    if ctx.phase_ratio >= 0.66:
        gates_passed.append("opening_phase")
    else:
        gates_failed.append("opening_phase")

    # Gate 3: Early move number
    if fullmove <= OPENING_MOVE_CUTOFF:
        gates_passed.append("early_move")
    else:
        gates_failed.append("early_move")

    # Gate 4: Development/repositioning intent (some improvement or neutral)
    developing = mobility_change >= -0.05 or center_change >= -0.05
    if developing:
        gates_passed.append("developing_intent")
    else:
        gates_failed.append("developing_intent")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # High confidence for clear opening maneuvers
        phase_bonus = min(0.4, (ctx.phase_ratio - 0.66) * 1.2)
        early_bonus = 0.3 if fullmove <= 10 else 0.2
        development_bonus = min(0.2, max(mobility_change, center_change) * 1.5)
        confidence = 0.4 + phase_bonus + early_bonus + development_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="maneuver_opening",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
