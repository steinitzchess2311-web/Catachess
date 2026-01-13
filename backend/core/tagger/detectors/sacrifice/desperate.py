"""Desperate sacrifice detectors - 2 in 1 file."""
from ...models import TagContext, TagEvidence
from ...detectors.helpers.sacrifice import is_sacrifice_candidate, SACRIFICE_EVAL_TOLERANCE

def detect_speculative_sacrifice(ctx: TagContext) -> TagEvidence:
    """Speculative sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    eval_loss = abs(ctx.delta_eval)
    evidence.update({"eval_loss": eval_loss})
    
    if is_sacrifice and eval_loss > SACRIFICE_EVAL_TOLERANCE:
        gates_passed.extend(["is_sacrifice", "speculative"])
        fired, confidence = True, 0.7
    else:
        gates_failed.append("is_sacrifice" if not is_sacrifice else "speculative")
        fired, confidence = False, 0.0
    
    return TagEvidence("speculative_sacrifice", fired, confidence, evidence, gates_passed, gates_failed)

def detect_desperate_sacrifice(ctx: TagContext) -> TagEvidence:
    """Desperate sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    eval_before = ctx.eval_before
    evidence.update({"eval_before": eval_before})
    
    if is_sacrifice and eval_before <= -3.0:
        gates_passed.extend(["is_sacrifice", "desperate_position"])
        fired, confidence = True, 0.8
    else:
        gates_failed.append("is_sacrifice" if not is_sacrifice else "desperate_position")
        fired, confidence = False, 0.0
    
    return TagEvidence("desperate_sacrifice", fired, confidence, evidence, gates_passed, gates_failed)

__all__ = ["detect_speculative_sacrifice", "detect_desperate_sacrifice"]
