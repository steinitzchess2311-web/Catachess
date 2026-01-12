"""Tension tag detectors - 4 detectors in 1 file."""
from core.tagger.models import TagContext, TagEvidence
from core.tagger.detectors.helpers.tension import check_symmetry_condition
from core.tagger.detectors.helpers.contact import contact_ratio

def detect_tension_creation(ctx: TagContext) -> TagEvidence:
    """Tension creation."""
    gates_passed, gates_failed, evidence = [], [], {}
    symmetry_before, sym_gap_before = check_symmetry_condition(ctx)
    # For symmetry_after, we'd need a full TagContext for the position after the move
    # For now, we'll use the contact ratio change as the primary indicator
    contact_delta = ctx.contact_ratio_played - ctx.contact_ratio_before
    evidence.update({"symmetry_before": symmetry_before, "contact_delta": contact_delta})
    
    # Tension creation: symmetry exists and contact increases
    if symmetry_before and contact_delta > 0.1:
        gates_passed.append("tension_created")
        fired, confidence = True, 0.8
    else:
        gates_failed.append("tension_created")
        fired, confidence = False, 0.0
    
    return TagEvidence("tension_creation", fired, confidence, evidence, gates_passed, gates_failed)

def detect_neutral_tension_creation(ctx: TagContext) -> TagEvidence:
    """Neutral tension."""
    gates_passed, gates_failed, evidence = [], [], {}
    contact_delta = ctx.contact_ratio_played - ctx.contact_ratio_before
    evidence.update({"contact_delta": contact_delta, "delta_eval": ctx.delta_eval})
    
    if contact_delta > 0.1 and abs(ctx.delta_eval) < 0.2:
        gates_passed.append("neutral_tension")
        fired, confidence = True, 0.7
    else:
        gates_failed.append("neutral_tension")
        fired, confidence = False, 0.0
    
    return TagEvidence("neutral_tension_creation", fired, confidence, evidence, gates_passed, gates_failed)

def detect_premature_attack(ctx: TagContext) -> TagEvidence:
    """Premature attack."""
    gates_passed, gates_failed, evidence = [], [], {}
    evidence.update({"tactical_weight": ctx.tactical_weight, "delta_eval": ctx.delta_eval})
    
    if ctx.tactical_weight >= 0.6 and ctx.delta_eval <= -0.5:
        gates_passed.append("premature")
        fired, confidence = True, 0.75
    else:
        gates_failed.append("premature")
        fired, confidence = False, 0.0
    
    return TagEvidence("premature_attack", fired, confidence, evidence, gates_passed, gates_failed)

def detect_file_pressure_c(ctx: TagContext) -> TagEvidence:
    """C-file pressure."""
    gates_passed, gates_failed, evidence = [], [], {}
    move_to_c = ctx.played_move.to_square % 8 == 2  # c-file
    evidence.update({"to_c_file": move_to_c, "delta_eval": ctx.delta_eval})
    
    if move_to_c and ctx.delta_eval >= -0.1:
        gates_passed.append("c_file_pressure")
        fired, confidence = True, 0.7
    else:
        gates_failed.append("c_file_pressure")
        fired, confidence = False, 0.0
    
    return TagEvidence("file_pressure_c", fired, confidence, evidence, gates_passed, gates_failed)

__all__ = ["detect_tension_creation", "detect_neutral_tension_creation", "detect_premature_attack", "detect_file_pressure_c"]
