"""
File Pressure C tag detector.

Detects when a player creates pressure specifically on the c-file,
which is often associated with queenside play and tension creation.

Conditions:
- Move involves the c-file (piece moves to c-file or from c-file)
- Pressure/control increase on c-file
- Part of tension creation or positional play

Evidence:
- move: The played move
- involves_c_file: Whether move involves c-file
- mobility_delta: Overall mobility change
- center_control_delta: Center control change (c-file is semi-central)
"""
import chess
from ...models import TagContext, TagEvidence


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect c-file pressure.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    move = ctx.played_move
    mobility_delta = ctx.component_deltas.get("mobility", 0.0)
    center_delta = ctx.component_deltas.get("center_control", 0.0)

    # Check if move involves c-file (file index 2)
    from_file = chess.square_file(move.from_square)
    to_file = chess.square_file(move.to_square)
    involves_c_file = from_file == 2 or to_file == 2

    # Store evidence
    evidence["from_square"] = chess.square_name(move.from_square)
    evidence["to_square"] = chess.square_name(move.to_square)
    evidence["involves_c_file"] = involves_c_file
    evidence["mobility_delta"] = mobility_delta
    evidence["center_control_delta"] = center_delta
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Move involves c-file
    if involves_c_file:
        gates_passed.append("involves_c_file")
    else:
        gates_failed.append("involves_c_file")

    # Gate 2: Increase in positional control (mobility or center)
    control_increase = mobility_delta > 0.05 or center_delta > 0.05
    if control_increase:
        gates_passed.append("control_increase")
    else:
        gates_failed.append("control_increase")

    # Gate 3: Not losing evaluation significantly
    eval_ok = ctx.delta_eval > -0.5
    if eval_ok:
        gates_passed.append("eval_acceptable")
    else:
        gates_failed.append("eval_acceptable")

    # Gate 4: In middlegame/opening (c-file pressure more relevant)
    relevant_phase = ctx.phase_ratio > 0.25
    if relevant_phase:
        gates_passed.append("relevant_phase")
    else:
        gates_failed.append("relevant_phase")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # Higher confidence for better control increases
        control_bonus = min(0.4, max(mobility_delta, center_delta) * 2.0)
        phase_bonus = min(0.2, ctx.phase_ratio * 0.3)
        confidence = 0.5 + control_bonus + phase_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="file_pressure_c",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
