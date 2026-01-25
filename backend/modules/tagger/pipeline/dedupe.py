"""
Dedupe helpers for tagger pipeline.
"""
from __future__ import annotations

import hashlib
from typing import Dict, Iterable

from modules.tagger.utils import normalize_name


def compute_game_hash(headers: Dict[str, str], moves_uci: Iterable[str]) -> str:
    """
    Compute a stable game hash from normalized headers and mainline moves.
    """
    fields = ["White", "Black", "Date", "Event", "Result"]
    header_bits = []
    for key in fields:
        value = headers.get(key, "") or ""
        if key in ("White", "Black"):
            header_bits.append(normalize_name(value))
        else:
            header_bits.append(value.strip().lower())

    moves_bit = " ".join(moves_uci).strip().lower()
    payload = "|".join(header_bits + [moves_bit])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
