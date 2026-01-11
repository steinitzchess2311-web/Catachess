"""
Storage integrity checking.

Provides hash calculation and verification for PGN content.
"""

import hashlib


def calculate_sha256(content: str | bytes) -> str:
    """
    Calculate SHA-256 hash of content.

    Args:
        content: Content to hash (string or bytes)

    Returns:
        Hexadecimal hash string
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    return hashlib.sha256(content).hexdigest()


def verify_hash(content: str | bytes, expected_hash: str) -> bool:
    """
    Verify content matches expected hash.

    Args:
        content: Content to verify
        expected_hash: Expected SHA-256 hash

    Returns:
        True if hash matches
    """
    actual_hash = calculate_sha256(content)
    return actual_hash == expected_hash


def calculate_size(content: str | bytes) -> int:
    """
    Calculate size of content in bytes.

    Args:
        content: Content to measure

    Returns:
        Size in bytes
    """
    if isinstance(content, str):
        content = content.encode("utf-8")

    return len(content)
