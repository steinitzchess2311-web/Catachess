"""Initiative tag detectors - 3 detectors in 1 file."""
from ...models import TagContext, TagEvidence

def detect_initiative_exploitation(ctx: TagContext) -> TagEvidence:
    """Initiative exploitation: eval +0.5, mobility >0."""
    gates_passed, gates_failed, evidence = [], [], {}
    
    mobility_delta = ctx.metrics_played.get("mobility", 0) - ctx.metrics_before.get("mobility", 0)
    evidence.update({"delta_eval": ctx.delta_eval, "mobility_delta": mobility_delta})
    
    if ctx.delta_eval >= 0.5:
        gates_passed.append("eval_gain")
    else:
        gates_failed.append("eval_gain")
    
    if mobility_delta > 0:
        gates_passed.append("mobility_gain")
    else:
        gates_failed.append("mobility_gain")
    
    fired = len(gates_passed) == 2
    confidence = 0.7 + min(0.3, ctx.delta_eval * 0.2) if fired else 0.0
    
    return TagEvidence("initiative_exploitation", fired, min(1.0, confidence), evidence, gates_passed, gates_failed)

def detect_initiative_attempt(ctx: TagContext) -> TagEvidence:
    """Initiative attempt: active try but unsuccessful."""
    gates_passed, gates_failed, evidence = [], [], {}
    
    mobility_delta = ctx.metrics_played.get("mobility", 0) - ctx.metrics_before.get("mobility", 0)
    evidence.update({"delta_eval": ctx.delta_eval, "mobility_delta": mobility_delta, "tactical_weight": ctx.tactical_weight})
    
    if ctx.tactical_weight >= 0.5:
        gates_passed.append("tactical_move")
    else:
        gates_failed.append("tactical_move")
    
    if -0.5 < ctx.delta_eval < 0.5:
        gates_passed.append("neutral_result")
    else:
        gates_failed.append("neutral_result")
    
    fired = len(gates_passed) == 2
    confidence = 0.6 if fired else 0.0
    
    return TagEvidence("initiative_attempt", fired, confidence, evidence, gates_passed, gates_failed)

def detect_deferred_initiative(ctx: TagContext) -> TagEvidence:
    """Deferred initiative: quiet, stable preparation."""
    gates_passed, gates_failed, evidence = [], [], {}
    
    evidence.update({"delta_eval": ctx.delta_eval, "tactical_weight": ctx.tactical_weight, "is_capture": ctx.is_capture})
    
    if not ctx.is_capture and not ctx.is_check:
        gates_passed.append("quiet_move")
    else:
        gates_failed.append("quiet_move")
    
    if -0.15 <= ctx.delta_eval <= 0.15:
        gates_passed.append("stable_eval")
    else:
        gates_failed.append("stable_eval")
    
    if ctx.tactical_weight < 0.4:
        gates_passed.append("positional")
    else:
        gates_failed.append("positional")
    
    fired = len(gates_passed) == 3
    confidence = 0.7 if fired else 0.0
    
    return TagEvidence("deferred_initiative", fired, confidence, evidence, gates_passed, gates_failed)

__all__ = ["detect_initiative_exploitation", "detect_initiative_attempt", "detect_deferred_initiative"]
