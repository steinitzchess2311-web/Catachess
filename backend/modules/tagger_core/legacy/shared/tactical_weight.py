"""
Tactical weight computation for chess positions.

Tactical weight measures how "tactical" a position is based on multiple factors:
- Evaluation swings (delta_eval)
- Depth-dependent score changes
- Contact ratio (captures/checks)
- Metric changes (tactics, structure)
- Forcing moves present
- Mate threats

Higher tactical weight (closer to 1.0) indicates more tactical complexity.
Lower tactical weight (closer to 0.0) indicates more quiet/positional play.
"""
import math


def _sigmoid(value: float) -> float:
    """Sigmoid activation function: maps (-inf, +inf) to (0, 1)."""
    return 1.0 / (1.0 + math.exp(-value))


def compute_tactical_weight(
    delta_eval_cp: int,
    delta_tactics: float,
    delta_structure: float,
    depth_jump_cp: int,
    deepening_gain_cp: int,
    score_gap_cp: int,
    contact_ratio: float,
    phase_ratio: float,
    best_is_forcing: bool,
    played_is_forcing: bool,
    mate_threat: bool,
) -> float:
    """
    Compute tactical weight for a position.

    Args:
        delta_eval_cp: Evaluation change (played - before) in centipawns
        delta_tactics: Change in tactics metric (played - before)
        delta_structure: Change in structure metric (played - before)
        depth_jump_cp: Score change with deeper analysis
        deepening_gain_cp: Additional gain from deepening
        score_gap_cp: Gap between best and second-best move
        contact_ratio: Proportion of contact moves (0.0-1.0)
        phase_ratio: Game phase (0.0=endgame, 1.0=opening)
        best_is_forcing: Whether best move is forcing (capture/check/threat)
        played_is_forcing: Whether played move is forcing
        mate_threat: Whether there's a mate threat

    Returns:
        Tactical weight in range 0.0-1.0 (sigmoid output)
        - Higher values = more tactical
        - Lower values = more positional/quiet
    """
    # Normalize each component to contribute to overall score
    eval_component = abs(delta_eval_cp) / 120.0
    depth_component = max(0.0, depth_jump_cp) / 120.0
    deepening_component = max(0.0, deepening_gain_cp) / 90.0
    gap_component = max(0.0, score_gap_cp) / 80.0
    tactics_component = abs(delta_tactics)
    contact_component = contact_ratio
    forcing_component = 0.5 if best_is_forcing else 0.0
    response_penalty = 0.25 if best_is_forcing and not played_is_forcing else 0.0
    mate_component = 0.8 if mate_threat else 0.0
    phase_penalty = (1.0 - phase_ratio) * 0.7  # Reduce in endgame
    structure_penalty = max(0.0, abs(delta_structure) - 0.1)

    # Weighted sum of components (weights from legacy)
    raw_score = (
        0.45 * eval_component
        + 0.75 * depth_component
        + 0.65 * deepening_component
        + 0.9 * gap_component
        + 1.2 * tactics_component  # Strongest signal
        + 0.7 * contact_component
        + forcing_component
        + mate_component
        - 0.9 * structure_penalty
        - phase_penalty
        - response_penalty
    )

    # Apply sigmoid with offset to map to 0-1 range
    # Offset of -1.3 means raw_score needs to be positive to get weight > 0.5
    return _sigmoid(raw_score - 1.3)


__all__ = ["compute_tactical_weight"]
