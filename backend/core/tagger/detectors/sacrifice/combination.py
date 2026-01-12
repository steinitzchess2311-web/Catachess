"""Combination sacrifice detectors - 2 in 1 file."""
from core.tagger.models import TagContext, TagEvidence
from core.tagger.detectors.helpers.sacrifice import is_sacrifice_candidate

def detect_tactical_combination_sacrifice(ctx: TagContext) -> TagEvidence:
    """Combination sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    evidence.update({"tactical_weight": ctx.tactical_weight})
    
    if is_sacrifice and ctx.tactical_weight >= 0.7:
        gates_passed.extend(["is_sacrifice", "high_tactics"])
        fired, confidence = True, 0.8
    else:
        gates_failed.append("is_sacrifice" if not is_sacrifice else "high_tactics")
        fired, confidence = False, 0.0
    
    return TagEvidence("tactical_combination_sacrifice", fired, confidence, evidence, gates_passed, gates_failed)

def detect_tactical_initiative_sacrifice(ctx: TagContext) -> TagEvidence:
    """Initiative sacrifice."""
    gates_passed, gates_failed, evidence = [], [], {}
    is_sacrifice, sac_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sac_evidence)
    mobility_delta = ctx.metrics_played.get("mobility", 0) - ctx.metrics_before.get("mobility", 0)
    evidence.update({"mobility_delta": mobility_delta})
    
    if is_sacrifice and mobility_delta > 0.3:
        gates_passed.extend(["is_sacrifice", "initiative_gain"])
        fired, confidence = True, 0.8
    else:
        gates_failed.append("is_sacrifice" if not is_sacrifice else "initiative_gain")
        fired, confidence = False, 0.0
    
    return TagEvidence("tactical_initiative_sacrifice", fired, confidence, evidence, gates_passed, gates_failed)

__all__ = ["detect_tactical_combination_sacrifice", "detect_tactical_initiative_sacrifice"]
