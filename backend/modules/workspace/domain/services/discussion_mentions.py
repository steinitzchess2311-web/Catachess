"""
Mention parsing helpers.
"""

import re


MENTION_PATTERN = re.compile(r"@([A-Za-z0-9_-]+)")


def extract_mentions(text: str) -> list[str]:
    """Extract unique mentions from text."""
    if not text:
        return []
    return list({match.group(1) for match in MENTION_PATTERN.finditer(text)})
