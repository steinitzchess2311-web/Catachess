"""
Control over Dynamics v2 detector module.

Detects moves that control game dynamics through:
- Prophylaxis
- Piece Control
- Pawn Control
- Simplification
"""
from .detector import ControlOverDynamicsV2Detector
from .models import CoDContext, CoDMetrics
from .result import CoDResult, CoDSubtype
from .thresholds import CoDThresholds, get_thresholds
from .config import is_cod_v2_enabled

__all__ = [
    "ControlOverDynamicsV2Detector",
    "CoDContext",
    "CoDMetrics",
    "CoDResult",
    "CoDSubtype",
    "CoDThresholds",
    "get_thresholds",
    "is_cod_v2_enabled",
]
