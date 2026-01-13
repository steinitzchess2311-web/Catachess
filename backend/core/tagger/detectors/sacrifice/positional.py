"""Positional sacrifice detectors - 4 in 1 file."""
from ...models import TagContext, TagEvidence
from ...detectors.helpers.sacrifice import is_sacrifice_candidate, SACRIFICE_EVAL_TOLERANCE, SACRIFICE_KING_DROP_THRESHOLD

def detect_positional_sacrifice(ctx: TagContext) -> TagEvidence:
    """Sound positional sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    
    if is_sacrifice:
        gates_passed.append("is_sacrifice")
    else:
        gates_failed.append("is_sacrifice")
        return TagEvidence("positional_sacrifice", False, 0.0, evidence, gates_passed, gates_failed)
    
    king_drop = ctx.opp_metrics_played.get("king_safety", 0) - ctx.opp_metrics_before.get("king_safety", 0)
    eval_loss = abs(ctx.delta_eval)
    evidence.update({"king_drop": king_drop, "eval_loss": eval_loss})
    
    if king_drop > SACRIFICE_KING_DROP_THRESHOLD:
        gates_passed.append("no_king_attack")
    else:
        gates_failed.append("no_king_attack")
    
    if eval_loss <= SACRIFICE_EVAL_TOLERANCE:
        gates_passed.append("sound")
    else:
        gates_failed.append("sound")
    
    fired = len(gates_passed) == 3
    confidence = 0.75 if fired else 0.0
    
    return TagEvidence("positional_sacrifice", fired, confidence, evidence, gates_passed, gates_failed)

def detect_positional_structure_sacrifice(ctx: TagContext) -> TagEvidence:
    """Structure sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    
    if not is_sacrifice:
        gates_failed.append("is_sacrifice")
        return TagEvidence("positional_structure_sacrifice", False, 0.0, evidence, gates_passed, gates_failed)
    
    gates_passed.append("is_sacrifice")
    structure_delta = ctx.metrics_played.get("structure", 0) - ctx.metrics_before.get("structure", 0)
    evidence.update({"structure_delta": structure_delta})
    
    if structure_delta > 0.2:
        gates_passed.append("structure_compensation")
        fired, confidence = True, 0.75
    else:
        gates_failed.append("structure_compensation")
        fired, confidence = False, 0.0
    
    return TagEvidence("positional_structure_sacrifice", fired, confidence, evidence, gates_passed, gates_failed)

def detect_positional_space_sacrifice(ctx: TagContext) -> TagEvidence:
    """Space sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    
    if not is_sacrifice:
        gates_failed.append("is_sacrifice")
        return TagEvidence("positional_space_sacrifice", False, 0.0, evidence, gates_passed, gates_failed)
    
    gates_passed.append("is_sacrifice")
    mobility_delta = ctx.metrics_played.get("mobility", 0) - ctx.metrics_before.get("mobility", 0)
    evidence.update({"mobility_delta": mobility_delta})
    
    if mobility_delta > 0.2:
        gates_passed.append("space_compensation")
        fired, confidence = True, 0.75
    else:
        gates_failed.append("space_compensation")
        fired, confidence = False, 0.0
    
    return TagEvidence("positional_space_sacrifice", fired, confidence, evidence, gates_passed, gates_failed)

__all__ = ["detect_positional_sacrifice", "detect_positional_structure_sacrifice", "detect_positional_space_sacrifice"]
