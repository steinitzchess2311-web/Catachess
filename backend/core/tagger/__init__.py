"""
Tagger module - Chess move semantic tagging system.

This module provides a comprehensive system for analyzing and tagging chess moves
with semantic labels based on tactical, positional, and strategic considerations.

Main entry point:
    tag_position() - Analyze a chess position and tag the played move

Data models:
    TagContext - Input context for tag detection
    TagEvidence - Detection result with confidence and evidence
    TagResult - Complete tagging result with all detected tags

Example usage:
    from backend.core.tagger import tag_position

    result = tag_position(
        engine_path="/usr/games/stockfish",
        fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        played_move_uci="e7e5",
        depth=14,
        multipv=6
    )

    print(f"First choice: {result.first_choice}")
    print(f"Tactical sacrifice: {result.tactical_sacrifice}")
    print(f"Delta eval: {result.delta_eval}")
"""
from .facade import tag_position
from .models import TagContext, TagEvidence, TagResult

__all__ = [
    "tag_position",
    "TagContext",
    "TagEvidence",
    "TagResult",
]

__version__ = "2.0.0"
__author__ = "Claude Code"
