"""
Structural Compromise Static tag detector.

Detects when a player weakens their pawn structure WITHOUT gaining dynamic
compensation. This is generally unfavorable.

Conditions:
- structure_delta < -0.15 (structure weakening)
- No significant dynamic compensation:
  - mobility_delta < 0.15 (no mobility gain)
  - tactics_delta < 0.20 (no tactical gain)
  - center_control_delta < 0.20 (no center gain)

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
    Detect structural compromise without dynamic compensation.

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

    # Gate 2: NO dynamic compensation
    has_compensation = (
        mobility_delta >= MOBILITY_GAIN_THRESHOLD
        or tactics_delta >= TACTICS_GAIN_THRESHOLD
        or center_delta >= CENTER_GAIN_THRESHOLD
    )

    if not has_compensation:
        gates_passed.append("no_compensation")
    else:
        gates_failed.append("no_compensation")

    # Fire if structure weakens AND no compensation
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for worse structure loss and more negative compensation
        structure_severity = min(0.4, abs(structure_delta - STRUCTURE_LOSS_THRESHOLD) * 1.5)
        # Penalty if mobility/tactics/center actually declined
        compensation_penalty = 0.0
        if mobility_delta < 0:
            compensation_penalty += min(0.2, abs(mobility_delta) * 0.5)
        if tactics_delta < 0:
            compensation_penalty += min(0.2, abs(tactics_delta) * 0.5)

        confidence = 0.5 + structure_severity + min(0.3, compensation_penalty)
    else:
        confidence = 0.0

    return TagEvidence(
        tag="structural_compromise_static",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
