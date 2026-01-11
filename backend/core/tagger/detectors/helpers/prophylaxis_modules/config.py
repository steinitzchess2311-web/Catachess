"""
Prophylaxis configuration and constants.

Matches rule_tagger2/legacy/prophylaxis.py:16-31 exactly.
"""
from dataclasses import dataclass


# Constants
FULL_MATERIAL_COUNT = 32
OPENING_MOVE_CUTOFF = 6  # Only block prophylaxis if fullmove < 6 AND all pieces present


@dataclass(frozen=True)
class ProphylaxisConfig:
    """
    Configuration for prophylaxis detection thresholds.

    All default values match rule_tagger2/legacy/prophylaxis.py exactly.

    Attributes:
        structure_min: Minimum structure improvement to count towards preventive score
        opp_mobility_drop: Threshold for opponent mobility restriction
        self_mobility_tol: Maximum self-mobility penalty tolerance
        preventive_trigger: Minimum preventive score to qualify as prophylaxis
        safety_cap: Maximum preventive score cap
        score_threshold: Minimum score for direct prophylaxis classification
        threat_depth: Engine depth for threat estimation (will be maxed with 8)
        threat_drop: Threshold for significant threat reduction
    """
    structure_min: float = 0.2
    opp_mobility_drop: float = 0.15
    self_mobility_tol: float = 0.3
    preventive_trigger: float = 0.16
    safety_cap: float = 0.6
    score_threshold: float = 0.20
    threat_depth: int = 6
    threat_drop: float = 0.35
