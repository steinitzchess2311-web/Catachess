"""
Structural Compromise Dynamic tag detector.

Detects when a player weakens their pawn structure but gains dynamic
compensation through increased mobility, tactics, or center control.

Conditions:
- structure_delta < -0.15 (structure weakening)
- At least one of:
  - mobility_delta >= 0.15 (mobility increase)
  - tactics_delta >= 0.20 (tactical opportunities)
  - center_control_delta >= 0.20 (center control increase)

Evidence:
- structure_delta: Change in structure metric
- mobility_delta: Change in mobility metric
- tactics_delta: Change in tactics metric
- center_control_delta: Change in center control metric
"""
from ...models import TagContext, TagEvidence


STRUCTURE_LOSS_THRESHOLD = -0.15
MOBILITY_GAIN_THRESHOLD = 0.15
TACTICS_GAIN_THRESHOLD = 0.20
CENTER_GAIN_THRESHOLD = 0.20


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect structural compromise with dynamic compensation.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    structure_delta = ctx.component_deltas.get("structure", 0.0)
    mobility_delta = ctx.component_deltas.get("mobility", 0.0)
    tactics_delta = ctx.component_deltas.get("tactics", 0.0)
    center_delta = ctx.component_deltas.get("center_control", 0.0)

    # Store evidence
    evidence["structure_delta"] = structure_delta
    evidence["mobility_delta"] = mobility_delta
    evidence["tactics_delta"] = tactics_delta
    evidence["center_control_delta"] = center_delta
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Structure weakening
    if structure_delta < STRUCTURE_LOSS_THRESHOLD:
        gates_passed.append("structure_weakening")
    else:
        gates_failed.append("structure_weakening")

    # Gate 2: Dynamic compensation (at least one source)
    has_compensation = False

    if mobility_delta >= MOBILITY_GAIN_THRESHOLD:
        gates_passed.append("mobility_compensation")
        has_compensation = True
    else:
        gates_failed.append("mobility_compensation")

    if tactics_delta >= TACTICS_GAIN_THRESHOLD:
        gates_passed.append("tactics_compensation")
        has_compensation = True
    else:
        gates_failed.append("tactics_compensation")

    if center_delta >= CENTER_GAIN_THRESHOLD:
        gates_passed.append("center_compensation")
        has_compensation = True
    else:
        gates_failed.append("center_compensation")

    # Fire if structure weakens AND has dynamic compensation
    fired = "structure_weakening" in gates_passed and has_compensation

    # Compute confidence
    if fired:
        # Higher confidence for more compensation sources
        compensation_score = (
            (mobility_delta / MOBILITY_GAIN_THRESHOLD if mobility_delta >= MOBILITY_GAIN_THRESHOLD else 0)
            + (tactics_delta / TACTICS_GAIN_THRESHOLD if tactics_delta >= TACTICS_GAIN_THRESHOLD else 0)
            + (center_delta / CENTER_GAIN_THRESHOLD if center_delta >= CENTER_GAIN_THRESHOLD else 0)
        )
        confidence = 0.5 + min(0.5, compensation_score * 0.2)
    else:
        confidence = 0.0

    return TagEvidence(
        tag="structural_compromise_dynamic",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
