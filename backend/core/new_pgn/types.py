"""
PGN data types for the new pipeline.
"""
from dataclasses import dataclass


# Type alias for PGN headers (tag pairs)
PGNHeader = dict[str, str]


@dataclass
class PGNGame:
    """
    Represents a single PGN game extracted from a multi-game PGN string.

    Attributes:
        headers: Dictionary of PGN tag pairs (e.g., {"Event": "...", "White": "..."})
        movetext: The SAN move sequence including variations and comments.
        raw: The original raw text for this game block.
        index: 1-based index of this game in the source PGN.
    """
    headers: PGNHeader
    movetext: str
    raw: str
    index: int
