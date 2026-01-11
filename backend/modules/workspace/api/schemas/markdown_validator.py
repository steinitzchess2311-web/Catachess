"""
Minimal markdown validation helpers.
"""

import re


_UNSAFE_HTML = re.compile(r"<\s*(script|iframe)", re.IGNORECASE)
_UNSAFE_ATTR = re.compile(r"onerror\s*=", re.IGNORECASE)


def validate_markdown(text: str) -> str:
    """Reject obvious unsafe HTML constructs."""
    if _UNSAFE_HTML.search(text) or _UNSAFE_ATTR.search(text):
        raise ValueError("Unsafe HTML is not allowed in markdown")
    return text
