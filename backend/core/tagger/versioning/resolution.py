"""
Tag resolution functions for alias handling.
"""
from typing import List, Optional

from .aliases import TAG_ALIASES


def get_canonical_name(tag: str) -> str:
    """
    Resolve tag to canonical form.

    Args:
        tag: Tag name (may be alias)

    Returns:
        Canonical tag name (or original if not aliased)
    """
    return TAG_ALIASES.get(tag, tag)


def resolve_tag_list(tags: List[str]) -> List[str]:
    """
    Resolve list of tags to canonical forms.

    Args:
        tags: List of tag names

    Returns:
        List of canonical tag names
    """
    return [get_canonical_name(tag) for tag in tags]


def is_alias(tag: str) -> bool:
    """
    Check if tag is an alias (non-canonical).

    Args:
        tag: Tag name

    Returns:
        True if alias, False if canonical or unknown
    """
    return tag in TAG_ALIASES


def get_aliases_for(canonical_tag: str) -> List[str]:
    """
    Get all aliases that map to a canonical tag.

    Args:
        canonical_tag: Canonical tag name

    Returns:
        List of aliases
    """
    return [
        alias for alias, canon in TAG_ALIASES.items()
        if canon == canonical_tag
    ]


__all__ = [
    "get_canonical_name",
    "resolve_tag_list",
    "is_alias",
    "get_aliases_for",
]
