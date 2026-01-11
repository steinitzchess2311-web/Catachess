"""
Configuration for CoD v2 detector.
Simple configuration without YAML dependencies.
"""
import os


def is_cod_v2_enabled() -> bool:
    """
    Check if CoD v2 is enabled via environment variable.

    Returns:
        True if COD_V2_ENABLED=1, False otherwise
    """
    return os.environ.get("COD_V2_ENABLED", "1") == "1"


def get_cooldown_plies() -> int:
    """Get cooldown period in plies (default 4)."""
    return int(os.environ.get("COD_COOLDOWN_PLIES", "4"))


__all__ = ["is_cod_v2_enabled", "get_cooldown_plies"]
