"""
Main Control over Dynamics v2 detector.
Orchestrates gates and subtype detection.
"""
from .models import CoDContext
from .result import CoDResult, CoDSubtype
from .thresholds import get_thresholds
from .gates import check_all_gates
from .subtypes import (
    detect_prophylaxis,
    detect_piece_control,
    detect_pawn_control,
    detect_simplification,
)


class ControlOverDynamicsV2Detector:
    """
    Control over Dynamics v2 Detector.

    Detects moves that control game dynamics through:
    1. Prophylaxis - Preventing opponent plans
    2. Piece Control - Restricting via piece activity
    3. Pawn Control - Restricting via pawn structure
    4. Simplification - Reducing complexity via exchanges
    """

    def __init__(self):
        """Initialize detector with thresholds."""
        self.thresholds = get_thresholds()
        self.name = "ControlOverDynamicsV2"
        self.version = "1.0.0"

    def detect(self, ctx: CoDContext) -> CoDResult:
        """
        Detect CoD in given context.

        Args:
            ctx: CoDContext with position and metrics

        Returns:
            CoDResult with detection outcome
        """
        # Step 1: Gate checks
        gates_passed, gates_failed = check_all_gates(ctx, self.thresholds)
        if not gates_passed:
            return CoDResult(
                detected=False,
                subtype=CoDSubtype.NONE,
                gates_passed={"gates": False},
                gates_failed=gates_failed,
                diagnostic={"reason": "failed_gates", "details": gates_failed},
            )

        # Step 2: Cooldown check
        if self._is_in_cooldown(ctx):
            return CoDResult(
                detected=False,
                subtype=CoDSubtype.NONE,
                gates_passed={"gates": True, "cooldown": False},
                gates_failed=["cooldown"],
                diagnostic={"reason": "cooldown", "ply": ctx.current_ply},
            )

        # Step 3: Try subtypes in priority order
        subtypes = [
            detect_prophylaxis,
            detect_piece_control,
            detect_pawn_control,
            detect_simplification,
        ]

        for detect_fn in subtypes:
            result = detect_fn(ctx, self.thresholds)
            if result.detected:
                result.gates_passed = {"gates": True, "cooldown": True}
                return result

        # No subtype detected
        return CoDResult.no_detection()

    def _is_in_cooldown(self, ctx: CoDContext) -> bool:
        """Check if move is in cooldown period."""
        if ctx.last_cod_ply < 0:
            return False

        cooldown_distance = ctx.current_ply - ctx.last_cod_ply
        return cooldown_distance < self.thresholds.cooldown_plies


__all__ = ["ControlOverDynamicsV2Detector"]
