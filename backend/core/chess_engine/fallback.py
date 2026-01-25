"""Fallback engine behavior for when remote engine is unavailable."""
from __future__ import annotations

from core.chess_basic.rule.api import generate_legal_moves
from core.chess_basic.utils.fen import parse_fen
from core.chess_engine.schemas import EngineLine, EngineResult
from core.log.log_chess_engine import logger


def analyze_legal_moves(fen: str, depth: int, multipv: int) -> EngineResult:
    """
    Fallback analysis: returns legal moves as PVs with neutral scores.

    This keeps the UI functional when the remote engine is unreachable.
    """
    try:
        state = parse_fen(fen)
        legal_moves = generate_legal_moves(state)
    except Exception as exc:
        logger.error(f"Fallback engine failed to parse FEN: {exc}")
        return EngineResult(lines=[], source="Fallback")

    if not legal_moves:
        return EngineResult(lines=[], source="Fallback")

    lines: list[EngineLine] = []
    for idx, move in enumerate(legal_moves[: max(1, multipv)]):
        lines.append(
            EngineLine(
                multipv=idx + 1,
                score=0,
                pv=[move.to_uci()],
            )
        )

    logger.warning(
        "Using fallback engine (legal moves only). depth=%s multipv=%s",
        depth,
        multipv,
    )
    return EngineResult(lines=lines, source="Fallback")
