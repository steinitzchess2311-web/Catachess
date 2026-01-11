"""
Prophylaxis detection modules (split for maintainability).

Each module is <100 lines for better code organization.
"""
from .config import ProphylaxisConfig, FULL_MATERIAL_COUNT, OPENING_MOVE_CUTOFF
from .candidate import is_prophylaxis_candidate, is_full_material
from .threat import estimate_opponent_threat
from .pattern import prophylaxis_pattern_reason
from .score import compute_preventive_score, compute_soft_weight, clamp_preventive_score
from .classify import classify_prophylaxis_quality

__all__ = [
    "ProphylaxisConfig",
    "FULL_MATERIAL_COUNT",
    "OPENING_MOVE_CUTOFF",
    "is_prophylaxis_candidate",
    "is_full_material",
    "estimate_opponent_threat",
    "prophylaxis_pattern_reason",
    "compute_preventive_score",
    "compute_soft_weight",
    "clamp_preventive_score",
    "classify_prophylaxis_quality",
]
