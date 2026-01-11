"""
Prophylaxis quality classification logic.

Matches rule_tagger2/legacy/prophylaxis.py:161-239 exactly.
"""
from typing import Optional, Tuple

from .config import ProphylaxisConfig


def classify_prophylaxis_quality(
    has_prophylaxis: bool,
    preventive_score: float,
    effective_delta: float,
    tactical_weight: float,
    soft_weight: float,
    *,
    eval_before_cp: int = 0,
    drop_cp: int = 0,
    threat_delta: float = 0.0,
    volatility_drop: float = 0.0,
    pattern_override: bool = False,
    config: ProphylaxisConfig,
) -> Tuple[Optional[str], float]:
    """
    Map prophylaxis heuristics to a quality label.

    V2 naming convention:
    - prophylactic_direct: direct tactical prevention with high weight
    - prophylactic_latent: latent positional prevention
    - prophylactic_meaningless: ineffective prophylaxis

    Args:
        has_prophylaxis: Whether prophylaxis is detected
        preventive_score: Opponent restriction score
        effective_delta: Effective evaluation delta
        tactical_weight: Tactical weight of position
        soft_weight: Soft positioning weight
        eval_before_cp: Evaluation before move (centipawns)
        drop_cp: Evaluation drop (centipawns)
        threat_delta: Threat reduction
        volatility_drop: Volatility reduction (centipawns)
        pattern_override: Whether pattern support exists
        config: Prophylaxis configuration

    Returns:
        Tuple of (label, score) where label is one of:
        - "prophylactic_direct"
        - "prophylactic_latent"
        - "prophylactic_meaningless"
        - None (not prophylaxis)
    """
    if not has_prophylaxis:
        return None, 0.0

    trigger = config.preventive_trigger
    safety_cap = config.safety_cap
    score_threshold = config.score_threshold
    fail_eval_band_cp = 200
    fail_drop_cp = 50

    # Check for failure case first
    if abs(eval_before_cp) <= fail_eval_band_cp and drop_cp < -fail_drop_cp:
        return "prophylactic_meaningless", 0.0

    # If preventive score is below trigger but pattern support exists, classify as latent
    # BUT only if there's also some meaningful signal (not just pattern alone)
    if preventive_score < trigger:
        if pattern_override:
            # Require additional signal beyond just pattern detection
            has_meaningful_signal = (
                threat_delta >= 0.05
                or volatility_drop >= 15.0
                or soft_weight >= 0.3
                or preventive_score >= trigger * 0.5
            )

            if has_meaningful_signal:
                latent_base = 0.45
                latent_score = max(latent_base, soft_weight * 0.8, preventive_score * 2.0)
                return "prophylactic_latent", round(min(latent_score, safety_cap), 3)
        return None, 0.0

    # Convert volatility drop to a normalized signal (0-1 scale)
    volatility_signal = max(0.0, min(1.0, volatility_drop / 40.0))
    threat_signal = max(0.0, threat_delta)
    soft_signal = max(0.0, soft_weight)

    direct_gate = (
        preventive_score >= (trigger + 0.02)
        or threat_signal >= max(config.threat_drop * 0.85, 0.2)
        or (soft_signal >= 0.65 and tactical_weight <= 0.6)
        or volatility_signal >= 0.65
    )

    if direct_gate:
        direct_score = max(score_threshold, preventive_score, soft_signal, threat_signal, 0.75)
        label = "prophylactic_direct"
        final_score = round(min(direct_score, safety_cap), 3)
    else:
        latent_base = 0.55 if effective_delta < 0 else 0.45
        latent_score = max(latent_base, preventive_score * 0.9, soft_signal)
        label = "prophylactic_latent"
        final_score = round(min(latent_score, safety_cap), 3)

    # Final failure check
    if abs(eval_before_cp) <= fail_eval_band_cp and drop_cp < -fail_drop_cp:
        return "prophylactic_meaningless", 0.0

    return label, final_score
