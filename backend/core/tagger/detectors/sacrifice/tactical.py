"""Tactical sacrifice detectors - 2 in 1 file."""
from core.tagger.models import TagContext, TagEvidence
from core.tagger.detectors.helpers.sacrifice import is_sacrifice_candidate, SACRIFICE_EVAL_TOLERANCE, SACRIFICE_KING_DROP_THRESHOLD

def detect_tactical_sacrifice(ctx: TagContext) -> TagEvidence:
    """Sound tactical sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    
    if is_sacrifice:
        gates_passed.append("is_sacrifice")
    else:
        gates_failed.append("is_sacrifice")
        return TagEvidence("tactical_sacrifice", False, 0.0, evidence, gates_passed, gates_failed)
    
    king_drop = ctx.opp_metrics_played.get("king_safety", 0) - ctx.opp_metrics_before.get("king_safety", 0)
    eval_loss = abs(ctx.delta_eval)
    evidence.update({"king_drop": king_drop, "eval_loss": eval_loss})
    
    if king_drop <= SACRIFICE_KING_DROP_THRESHOLD:
        gates_passed.append("king_attack")
    else:
        gates_failed.append("king_attack")
    
    if eval_loss <= SACRIFICE_EVAL_TOLERANCE:
        gates_passed.append("sound")
    else:
        gates_failed.append("sound")
    
    fired = len(gates_passed) == 3
    confidence = 0.7 + min(0.3, abs(king_drop) * 1.5) if fired else 0.0
    
    return TagEvidence("tactical_sacrifice", fired, min(1.0, confidence), evidence, gates_passed, gates_failed)

def detect_inaccurate_tactical_sacrifice(ctx: TagContext) -> TagEvidence:
    """Inaccurate tactical sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    
    if is_sacrifice:
        gates_passed.append("is_sacrifice")
    else:
        gates_failed.append("is_sacrifice")
        return TagEvidence("inaccurate_tactical_sacrifice", False, 0.0, evidence, gates_passed, gates_failed)
    
    king_drop = ctx.opp_metrics_played.get("king_safety", 0) - ctx.opp_metrics_before.get("king_safety", 0)
    eval_loss = abs(ctx.delta_eval)
    evidence.update({"king_drop": king_drop, "eval_loss": eval_loss})
    
    if king_drop <= SACRIFICE_KING_DROP_THRESHOLD:
        gates_passed.append("king_attack")
    else:
        gates_failed.append("king_attack")
    
    if eval_loss > SACRIFICE_EVAL_TOLERANCE:
        gates_passed.append("unsound")
    else:
        gates_failed.append("unsound")
    
    fired = len(gates_passed) == 3
    confidence = 0.7 if fired else 0.0
    
    return TagEvidence("inaccurate_tactical_sacrifice", fired, confidence, evidence, gates_passed, gates_failed)

__all__ = ["detect_tactical_sacrifice", "detect_inaccurate_tactical_sacrifice"]
