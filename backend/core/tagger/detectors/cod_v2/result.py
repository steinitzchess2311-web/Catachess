"""
CoD v2 result types and subtypes.
Keep under 100 lines.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class CoDSubtype(Enum):
    """Control over Dynamics subtypes."""
    PROPHYLAXIS = "prophylaxis"
    PIECE_CONTROL = "piece_control"
    PAWN_CONTROL = "pawn_control"
    SIMPLIFICATION = "simplification"
    NONE = "none"


@dataclass
class CoDResult:
    """
    Result of CoD v2 detection.
    Contains detection outcome, subtype, and diagnostics.
    """
    detected: bool
    subtype: CoDSubtype
    confidence: float = 0.0

    # Gates and diagnostics
    gates_passed: Dict[str, bool] = field(default_factory=dict)
    gates_failed: List[str] = field(default_factory=list)
    diagnostic: Dict[str, Any] = field(default_factory=dict)

    # Evidence trail
    evidence: Dict[str, Any] = field(default_factory=dict)
    thresholds_used: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "detected": self.detected,
            "subtype": self.subtype.value if self.subtype else None,
            "confidence": round(self.confidence, 3),
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "diagnostic": self.diagnostic,
            "evidence": self.evidence,
        }

    @classmethod
    def no_detection(cls) -> "CoDResult":
        """Create a no-detection result."""
        return cls(
            detected=False,
            subtype=CoDSubtype.NONE,
            confidence=0.0,
        )


__all__ = ["CoDSubtype", "CoDResult"]
