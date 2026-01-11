"""
Tag alias mappings for backward compatibility.
Maps old/deprecated tag names to canonical forms.
"""
from typing import Dict

# Spelling corrections
SPELLING_ALIASES: Dict[str, str] = {
    "tension_criation": "tension_creation",
    "tension_creatoin": "tension_creation",
    "netural_tension": "neutral_tension_creation",
    "prophilaxis": "prophylactic_move",
    "prophilactic": "prophylactic_move",
    "innitiative": "initiative_attempt",
    "control_over_dynamic": "control_over_dynamics",
    "manuever": "constructive_maneuver",
    "manouver": "constructive_maneuver",
    "sacrafice": "tactical_sacrifice",
    "sacrifise": "tactical_sacrifice",
}

# Convention aliases (short forms, standardization)
CONVENTION_ALIASES: Dict[str, str] = {
    "tension": "tension_creation",
    "neutral_tension": "neutral_tension_creation",
    "initiative": "initiative_attempt",
    "maneuver": "constructive_maneuver",
    "prophylaxis": "prophylactic_move",
    "control": "control_over_dynamics",
    "cod": "control_over_dynamics",
    "positional_sac": "positional_sacrifice",
    "speculative_sac": "speculative_sacrifice",
    "desperate_sac": "desperate_sacrifice",
    "inaccurate_sac": "inaccurate_tactical_sacrifice",
    "failed_maneuver": "misplaced_maneuver",
}

# Deprecated tag migrations
DEPRECATED_ALIASES: Dict[str, str] = {
    "prophylactic_strong": "prophylactic_direct",
    "prophylactic_soft": "prophylactic_latent",
}

# Combined alias map (all sources)
TAG_ALIASES: Dict[str, str] = {
    **SPELLING_ALIASES,
    **CONVENTION_ALIASES,
    **DEPRECATED_ALIASES,
}


__all__ = [
    "TAG_ALIASES",
    "SPELLING_ALIASES",
    "CONVENTION_ALIASES",
    "DEPRECATED_ALIASES",
]
