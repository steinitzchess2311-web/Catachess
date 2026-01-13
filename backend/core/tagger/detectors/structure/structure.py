"""Structure tag detectors - 3 detectors in 1 file."""
import chess
from ...models import TagContext, TagEvidence

def detect_structural_integrity(ctx: TagContext) -> TagEvidence:
    """Structural integrity: +0.25 structure, ≤+0.1 tactics."""
    gates_passed, gates_failed, evidence = [], [], {}
    
    structure_delta = ctx.metrics_played.get("structure", 0) - ctx.metrics_before.get("structure", 0)
    tactics_delta = ctx.metrics_played.get("tactics", 0) - ctx.metrics_before.get("tactics", 0)
    evidence.update({"structure_delta": structure_delta, "tactics_delta": tactics_delta})
    
    if structure_delta >= 0.25:
        gates_passed.append("structure_gain")
    else:
        gates_failed.append("structure_gain")
    
    if tactics_delta <= 0.1:
        gates_passed.append("limited_tactics")
    else:
        gates_failed.append("limited_tactics")
    
    fired = len(gates_passed) == 2
    confidence = 0.7 + min(0.3, structure_delta * 0.5) if fired else 0.0
    
    return TagEvidence("structural_integrity", fired, min(1.0, confidence), evidence, gates_passed, gates_failed)

def detect_structural_compromise_dynamic(ctx: TagContext) -> TagEvidence:
    """Structural compromise with compensation."""
    gates_passed, gates_failed, evidence = [], [], {}
    
    structure_delta = ctx.metrics_played.get("structure", 0) - ctx.metrics_before.get("structure", 0)
    mobility_delta = ctx.metrics_played.get("mobility", 0) - ctx.metrics_before.get("mobility", 0)
    evidence.update({"structure_delta": structure_delta, "mobility_delta": mobility_delta})
    
    if structure_delta <= -0.2:
        gates_passed.append("structure_loss")
    else:
        gates_failed.append("structure_loss")
    
    if mobility_delta >= 0.15 or ctx.delta_eval >= -0.3:
        gates_passed.append("has_compensation")
    else:
        gates_failed.append("has_compensation")
    
    fired = len(gates_passed) == 2
    confidence = 0.6 + min(0.3, mobility_delta * 0.5) if fired else 0.0
    
    return TagEvidence("structural_compromise_dynamic", fired, min(1.0, confidence), evidence, gates_passed, gates_failed)

def detect_structural_compromise_static(ctx: TagContext) -> TagEvidence:
    """Structural compromise without compensation."""
    gates_passed, gates_failed, evidence = [], [], {}
    
    structure_delta = ctx.metrics_played.get("structure", 0) - ctx.metrics_before.get("structure", 0)
    mobility_delta = ctx.metrics_played.get("mobility", 0) - ctx.metrics_before.get("mobility", 0)
    evidence.update({"structure_delta": structure_delta, "mobility_delta": mobility_delta})
    
    if structure_delta <= -0.2:
        gates_passed.append("structure_loss")
    else:
        gates_failed.append("structure_loss")
    
    if mobility_delta < 0.15 and ctx.delta_eval < -0.3:
        gates_passed.append("no_compensation")
    else:
        gates_failed.append("no_compensation")
    
    fired = len(gates_passed) == 2
    confidence = 0.7 if fired else 0.0
    
    return TagEvidence("structural_compromise_static", fired, confidence, evidence, gates_passed, gates_failed)

__all__ = ["detect_structural_integrity", "detect_structural_compromise_dynamic", "detect_structural_compromise_static"]
