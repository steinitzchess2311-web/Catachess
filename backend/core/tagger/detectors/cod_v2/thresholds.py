"""
Threshold definitions for CoD v2.
Values match rule_tagger2 exactly.
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CoDThresholds:
    """
    Thresholds for Control over Dynamics detection.
    All values copied from rule_tagger2/cod_v2 for parity.
    """
    # Tactical gating
    tactical_weight_ceiling: float = 0.65
    mate_threat_gate: bool = True
    blunder_threat_thresh: float = 0.8

    # Volatility
    volatility_drop_cp: float = 80.0

    # Mobility
    opp_mobility_drop: float = 0.15

    # Evaluation
    eval_drop: float = 0.5

    # King safety
    king_safety_thresh: float = 0.15
    king_safety_tolerance: float = 0.05

    # Tension
    tension_delta_mid: float = 0.3
    tension_delta_end: float = 0.15

    # Simplification
    simplify_min_exchange: float = 3.0

    # Cooldown
    cooldown_plies: int = 4

    # Prophylaxis
    preventive_trigger: float = 0.25
    threat_drop_min: float = 0.2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "tactical_weight_ceiling": self.tactical_weight_ceiling,
            "volatility_drop_cp": self.volatility_drop_cp,
            "opp_mobility_drop": self.opp_mobility_drop,
            "eval_drop": self.eval_drop,
            "cooldown_plies": self.cooldown_plies,
            "preventive_trigger": self.preventive_trigger,
        }


# Default thresholds instance
DEFAULT_THRESHOLDS = CoDThresholds()


def get_thresholds() -> CoDThresholds:
    """Get CoD thresholds (returns default for now)."""
    return DEFAULT_THRESHOLDS


__all__ = ["CoDThresholds", "DEFAULT_THRESHOLDS", "get_thresholds"]
