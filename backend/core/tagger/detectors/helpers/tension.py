"""
Tension detection helper functions.

Provides helper functions for detecting tension creation patterns in chess
positions. Tension occurs when both players increase their activity symmetrically,
often accompanied by contact ratio increases.

This is a simplified version of the legacy tension detection logic.
Full complexity available in legacy core_v8.py lines 1700-1900.
"""
from typing import Tuple
from ...models import TagContext
from ...config.engine import (
    TENSION_EVAL_MIN,
    TENSION_EVAL_MAX,
    TENSION_SYMMETRY_TOL,
)


def check_symmetry_condition(ctx: TagContext) -> Tuple[bool, float]:
    """
    Check if mobility changes are symmetrical (both players increasing).

    Args:
        ctx: Tag detection context

    Returns:
        Tuple of (is_symmetrical, symmetry_gap)
    """
    mobility_self = ctx.component_deltas.get("mobility", 0.0)
    mobility_opp = ctx.opp_component_deltas.get("mobility", 0.0)

    # Both should be increasing (positive)
    both_increasing = mobility_self > 0 and mobility_opp > 0

    # Check symmetry (magnitudes should be similar)
    symmetry_gap = abs(abs(mobility_self) - abs(mobility_opp))
    is_symmetrical = symmetry_gap <= TENSION_SYMMETRY_TOL

    return both_increasing and is_symmetrical, symmetry_gap


def check_contact_increase(ctx: TagContext) -> Tuple[bool, float]:
    """
    Check if contact ratio increased significantly.

    Args:
        ctx: Tag detection context

    Returns:
        Tuple of (has_increase, contact_delta)
    """
    contact_delta = ctx.contact_ratio_played - ctx.contact_ratio_before

    # Significant increase threshold
    CONTACT_INCREASE_THRESHOLD = 0.05

    return contact_delta >= CONTACT_INCREASE_THRESHOLD, contact_delta


def check_eval_band(ctx: TagContext) -> bool:
    """
    Check if evaluation is in acceptable range for tension.

    Args:
        ctx: Tag detection context

    Returns:
        True if eval is in tension band
    """
    return TENSION_EVAL_MIN <= ctx.delta_eval <= TENSION_EVAL_MAX


def mobility_magnitudes_sufficient(ctx: TagContext, threshold: float = 0.15) -> bool:
    """
    Check if both players have sufficient mobility changes.

    Args:
        ctx: Tag detection context
        threshold: Minimum mobility change magnitude

    Returns:
        True if both have sufficient magnitude
    """
    mobility_self = abs(ctx.component_deltas.get("mobility", 0.0))
    mobility_opp = abs(ctx.opp_component_deltas.get("mobility", 0.0))

    return mobility_self >= threshold and mobility_opp >= threshold


def is_asymmetrical_tension(ctx: TagContext) -> bool:
    """
    Check for asymmetrical tension (one side dominates).

    Args:
        ctx: Tag detection context

    Returns:
        True if tension is asymmetrical
    """
    mobility_self = ctx.component_deltas.get("mobility", 0.0)
    mobility_opp = ctx.opp_component_deltas.get("mobility", 0.0)

    # Asymmetrical: magnitudes differ significantly
    symmetry_gap = abs(abs(mobility_self) - abs(mobility_opp))

    # Or one is negative (decreasing) while other is positive
    opposite_directions = (mobility_self > 0) != (mobility_opp > 0)

    return symmetry_gap > TENSION_SYMMETRY_TOL or opposite_directions


__all__ = [
    "check_symmetry_condition",
    "check_contact_increase",
    "check_eval_band",
    "mobility_magnitudes_sufficient",
    "is_asymmetrical_tension",
]
