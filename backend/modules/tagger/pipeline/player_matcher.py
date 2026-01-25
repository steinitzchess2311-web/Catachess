"""
Player matcher for tagger pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional

from models.tagger import PlayerProfile
from modules.tagger.utils import normalize_name


@dataclass
class MatchResult:
    color: Optional[str]
    candidates: List[str]
    reason: Optional[str] = None


def _normalized_aliases(player: PlayerProfile) -> List[str]:
    values = [player.display_name] + (player.aliases or [])
    return [normalize_name(v) for v in values if v]


def _fuzzy_match(name: str, candidates: List[str], threshold: float = 0.9) -> bool:
    if not name:
        return False
    for candidate in candidates:
        ratio = SequenceMatcher(None, name, candidate).ratio()
        if ratio >= threshold:
            return True
    return False


def match_player_color(player: PlayerProfile, white_name: str | None, black_name: str | None) -> MatchResult:
    """
    Match player to PGN headers to determine color.
    Returns MatchResult with color in {"white","black"} or None.
    """
    if not white_name or not black_name:
        return MatchResult(color=None, candidates=[white_name or "", black_name or ""], reason="header_missing")

    normalized_targets = _normalized_aliases(player)
    white_norm = normalize_name(white_name)
    black_norm = normalize_name(black_name)

    white_match = white_norm in normalized_targets or _fuzzy_match(white_norm, normalized_targets)
    black_match = black_norm in normalized_targets or _fuzzy_match(black_norm, normalized_targets)

    if white_match and black_match:
        return MatchResult(color=None, candidates=[white_name, black_name], reason="ambiguous")
    if white_match:
        return MatchResult(color="white", candidates=[white_name, black_name])
    if black_match:
        return MatchResult(color="black", candidates=[white_name, black_name])

    return MatchResult(color=None, candidates=[white_name, black_name], reason="no_match")
