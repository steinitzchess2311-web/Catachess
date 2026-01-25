"""
Shared utilities for tagger module.
"""
import unicodedata


def normalize_name(name: str) -> str:
    """规范化棋手名称"""
    normalized = unicodedata.normalize("NFKC", name.lower().strip())
    return "".join(c for c in normalized if c.isalnum() or c.isspace()).strip()
