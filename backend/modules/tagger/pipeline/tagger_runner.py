"""
Tagger runner for tagger pipeline.
"""
from __future__ import annotations

import os
from typing import List, Tuple

import requests

from core.tagger.facade import tag_position
from core.tagger.tagging import apply_suppression_rules, get_primary_tags
from core.tagger.config.engine import DEFAULT_DEPTH, DEFAULT_MULTIPV


TAGGER_MODE_BLACKBOX = "blackbox"
TAGGER_MODE_CUT = "cut"
BLACKBOX_ENV_KEYS = ("TAGGER_BLACKBOX_URL", "BLACKBOX_TAGGER_URL", "RULE_TAGGER_URL")


def _resolve_blackbox_url() -> str:
    for key in BLACKBOX_ENV_KEYS:
        value = os.getenv(key)
        if value:
            return value
    return ""


def _normalize_blackbox_url(base_url: str) -> str:
    url = base_url.rstrip("/")
    if url.endswith("/tagger/analyze"):
        return url
    return f"{url}/tagger/analyze"


def _extract_blackbox_tags(payload: dict) -> list[str]:
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("tags_list"), list):
        return payload.get("tags_list") or []
    if isinstance(payload.get("tags"), list):
        return payload.get("tags") or []
    tags_obj = payload.get("tags") or {}
    if isinstance(tags_obj, dict):
        if isinstance(tags_obj.get("primary"), list):
            return tags_obj.get("primary") or []
        if isinstance(tags_obj.get("active"), list):
            return tags_obj.get("active") or []
    if isinstance(payload.get("primary_tags"), list):
        return payload.get("primary_tags") or []
    if isinstance(payload.get("active_tags"), list):
        return payload.get("active_tags") or []
    return []


def _tag_move_blackbox_http(fen: str, move_uci: str) -> list[str]:
    base_url = _resolve_blackbox_url()
    if not base_url:
        raise RuntimeError("Blackbox tagger URL is not configured.")
    url = _normalize_blackbox_url(base_url)
    headers = {}
    token = os.getenv("TAGGER_API_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(
        url,
        json={
            "fen": fen,
            "move": move_uci,
            "played_move_uci": move_uci,
            "depth": DEFAULT_DEPTH,
            "multipv": DEFAULT_MULTIPV,
        },
        timeout=15,
        headers=headers,
    )
    resp.raise_for_status()
    payload = resp.json()
    tags = _extract_blackbox_tags(payload)
    return tags


def _tag_move_blackbox_local(fen: str, move_uci: str) -> list[str]:
    from core.blackbox_tagger import tag_position as blackbox_tag_position

    result = blackbox_tag_position(
        fen=fen,
        played_move_uci=move_uci,
        depth=DEFAULT_DEPTH,
        multipv=DEFAULT_MULTIPV,
        engine_mode="http",
    )
    return get_primary_tags(result)


def tag_move(
    fen: str,
    move_uci: str,
    *,
    tagger_mode: str = TAGGER_MODE_CUT,
) -> Tuple[List[str], int, int]:
    """
    Tag a move, returning (primary_tags, depth, multipv).
    """
    mode = tagger_mode or TAGGER_MODE_CUT
    if mode == TAGGER_MODE_BLACKBOX:
        if _resolve_blackbox_url():
            all_tags = _tag_move_blackbox_http(fen, move_uci)
        else:
            all_tags = _tag_move_blackbox_local(fen, move_uci)
    else:
        result = tag_position(
            fen=fen,
            played_move_uci=move_uci,
            depth=DEFAULT_DEPTH,
            multipv=DEFAULT_MULTIPV,
            engine_mode="http",
        )
        all_tags = get_primary_tags(result)

    primary_tags, _ = apply_suppression_rules(all_tags)
    return primary_tags, DEFAULT_DEPTH, DEFAULT_MULTIPV
