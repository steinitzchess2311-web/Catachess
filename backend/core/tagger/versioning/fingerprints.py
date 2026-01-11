"""
Version fingerprinting for tagger outputs.
Detects which version generated a result by analyzing thresholds.
"""
from typing import Dict, Optional, Any


# Version fingerprints (threshold signatures)
FINGERPRINTS = {
    "v1.0.0-catachess": {
        "tension_mobility_min": 0.38,
        "contact_ratio_min": 0.04,
        "mate_threat_threshold": 9000,
        "coverage_delta_enabled": True,
        "cod_v2_enabled": True,
        "cooldown_plies": 4,
    },
}

# Fingerprint keys to check
FINGERPRINT_KEYS = [
    "tension_mobility_min",
    "contact_ratio_min",
    "mate_threat_threshold",
    "cod_v2_enabled",
    "cooldown_plies",
]


def infer_version(analysis_context: Dict[str, Any]) -> Optional[str]:
    """
    Infer tagger version from analysis context.

    Args:
        analysis_context: Analysis metadata dictionary

    Returns:
        Detected version string or None
    """
    if not analysis_context:
        return None

    # Check for explicit version field
    if "version" in analysis_context:
        return analysis_context["version"]

    # Try fingerprint matching
    engine_meta = analysis_context.get("engine_meta", {})
    cod_meta = engine_meta.get("cod_v2", {})

    candidates = []
    for version, fingerprint in FINGERPRINTS.items():
        score = 0

        # Check each fingerprint key
        for key in FINGERPRINT_KEYS:
            # Look in different metadata locations
            value = None
            if key in engine_meta:
                value = engine_meta[key]
            elif key in cod_meta:
                value = cod_meta[key]
            elif key in analysis_context:
                value = analysis_context[key]

            # Compare with fingerprint
            if value is not None:
                expected = fingerprint.get(key)
                if expected is not None:
                    if isinstance(expected, bool):
                        if value == expected:
                            score += 1
                    elif isinstance(expected, (int, float)):
                        if abs(value - expected) <= 1e-3:
                            score += 1

        candidates.append((score, version))

    # Return best match if confident
    candidates.sort(reverse=True)
    if candidates and candidates[0][0] >= 2:
        return candidates[0][1]

    return None


__all__ = ["FINGERPRINTS", "infer_version"]
