"""
Migration helpers for tag data conversion.
"""
from typing import Dict, Any, Optional

from .resolution import get_canonical_name


def migrate_tag_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate old tag data to use canonical names.

    Args:
        data: Dictionary with tag names as keys

    Returns:
        New dictionary with canonical tag names
    """
    migrated = {}
    for old_tag, value in data.items():
        canonical = get_canonical_name(old_tag)
        migrated[canonical] = value
    return migrated


def suggest_canonical(tag: str) -> Optional[str]:
    """
    Suggest canonical form for potentially malformed tag.

    Args:
        tag: Tag name

    Returns:
        Suggested canonical name or None
    """
    from .aliases import TAG_ALIASES

    # Try direct lookup
    if tag in TAG_ALIASES:
        return TAG_ALIASES[tag]

    # Try normalized lookup
    normalized = tag.lower().strip()
    if normalized in TAG_ALIASES:
        return TAG_ALIASES[normalized]

    # Try matching without underscores
    canonical_forms = set(TAG_ALIASES.values())
    for canonical in canonical_forms:
        if canonical.replace("_", "") == normalized.replace("_", ""):
            return canonical

    return None


__all__ = [
    "migrate_tag_data",
    "suggest_canonical",
]
