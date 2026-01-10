"""
5-dimensional position metrics computation.

Computes position evaluation across 5 dimensions:
- mobility: Piece mobility and activity
- center_control: Control of central squares
- king_safety: King safety score
- structure: Pawn structure quality
- tactics: Tactical opportunities

These metrics are used throughout tag detection for assessing position quality
and changes after moves.
"""
from typing import Dict, Tuple, Any
import chess
import sys
from pathlib import Path

# Add chess_evaluator to path if available
chess_evaluator_path = Path("/home/catadragon/Code/ChessorTag_final/chess_imitator/rule_tagger_lichessbot")
if chess_evaluator_path.exists() and str(chess_evaluator_path) not in sys.path:
    sys.path.insert(0, str(chess_evaluator_path))

try:
    from chess_evaluator import ChessEvaluator, pov
    HAS_EVALUATOR = True
except ImportError:
    HAS_EVALUATOR = False


# Style component keys matching legacy config
STYLE_COMPONENT_KEYS = ("mobility", "center_control", "king_safety", "structure", "tactics")


def evaluation_and_metrics(
    board: chess.Board,
    actor: chess.Color,
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, Any]]:
    """
    Compute 5-dimensional position metrics.

    Args:
        board: Chess board position
        actor: Color to evaluate for (WHITE or BLACK)

    Returns:
        Tuple of (metrics, opp_metrics, evaluation):
        - metrics: Actor's metrics {mobility, center_control, king_safety, structure, tactics}
        - opp_metrics: Opponent's metrics (negation of actor metrics)
        - evaluation: Full evaluation dict with detailed breakdown

    Each metric is normalized to roughly -1.0 to +1.0 range (though can exceed).
    Positive values favor the actor, negative favor the opponent.
    """
    if not HAS_EVALUATOR:
        # Fallback: return dummy metrics if evaluator not available
        metrics = {key: 0.0 for key in STYLE_COMPONENT_KEYS}
        opp_metrics = {key: 0.0 for key in STYLE_COMPONENT_KEYS}
        return metrics, opp_metrics, {}

    evaluation = ChessEvaluator(board).evaluate()
    comps = evaluation["components"]

    # Convert to actor's point of view and round to 3 decimals
    metrics = {key: round(pov(comps[key], actor), 3) for key in STYLE_COMPONENT_KEYS}
    opp_metrics = {key: round(-metrics[key], 3) for key in STYLE_COMPONENT_KEYS}

    return metrics, opp_metrics, evaluation


def metrics_delta(lhs: Dict[str, float], rhs: Dict[str, float]) -> Dict[str, float]:
    """
    Compute difference between two metric dicts.

    Args:
        lhs: Left-hand side metrics (typically "before" state)
        rhs: Right-hand side metrics (typically "after" state)

    Returns:
        Delta dict {key: rhs[key] - lhs[key]} for each component

    Positive delta = improvement in that dimension
    Negative delta = decline in that dimension
    """
    return {key: round(rhs.get(key, 0.0) - lhs.get(key, 0.0), 3) for key in STYLE_COMPONENT_KEYS}


__all__ = [
    "STYLE_COMPONENT_KEYS",
    "evaluation_and_metrics",
    "metrics_delta",
]
