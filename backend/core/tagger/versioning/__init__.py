"""
Versioning system for catachess tagger.
Tracks tagger output versions and supports compatibility.
"""

# Current version
CURRENT_VERSION = "v1.0.0-catachess"

# Supported versions (for backward compatibility)
SUPPORTED_VERSIONS = [
    "v1.0.0-catachess",
]

# Version metadata
VERSION_INFO = {
    "v1.0.0-catachess": {
        "date": "2026-01-10",
        "features": [
            "41_tag_detectors",
            "pipeline_system",
            "mate_threat_detection",
            "coverage_delta_computation",
            "cod_v2_full",
            "tag_suppression",
        ],
        "cod_subtypes": ["prophylaxis", "piece_control", "pawn_control", "simplification"],
        "schema_version": "1.0",
    },
}


def get_current_version() -> str:
    """Get current tagger version."""
    return CURRENT_VERSION


def get_version_info(version: str = None) -> dict:
    """
    Get version metadata.

    Args:
        version: Version string (defaults to current)

    Returns:
        Version info dictionary
    """
    if version is None:
        version = CURRENT_VERSION

    return VERSION_INFO.get(version, {})


def is_supported(version: str) -> bool:
    """Check if version is supported."""
    return version in SUPPORTED_VERSIONS


__all__ = [
    "CURRENT_VERSION",
    "SUPPORTED_VERSIONS",
    "VERSION_INFO",
    "get_current_version",
    "get_version_info",
    "is_supported",
]
