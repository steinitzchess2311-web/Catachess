"""
PGN serialization utilities.

Provides tools to convert between PGN text and variation tree structures.

DEPRECATED: Use backend.core.real_pgn for new PGN processing.
"""
import warnings

warnings.warn(
    "DEPRECATED: Use backend.core.real_pgn for new PGN processing.",
    DeprecationWarning,
    stacklevel=2,
)

from modules.workspace.pgn.serializer.to_tree import pgn_to_tree, VariationNode
from modules.workspace.pgn.serializer.to_pgn import tree_to_pgn

__all__ = ["pgn_to_tree", "tree_to_pgn", "VariationNode"]
