"""
Created at: 2026-07-08 23:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:05 EDT
Last Modified by: Codex

Tests for local server-side engine workers.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch

import pytest

os.environ.setdefault("ALLOW_CONFIG_WARNINGS", "1")
os.environ["DEBUG"] = "false"
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from core.chess_engine.local_workers import (
    AlphaZeroWorker,
    CrossProcessSlotLimiter,
    Lc0Worker,
    LocalStockfishWorker,
    parse_stockfish_info_lines,
)
from core.errors import ChessEngineError, ChessEngineTimeoutError


def test_parse_stockfish_info_lines_keeps_deepest_multipv() -> None:
    lines = parse_stockfish_info_lines(
        [
            "info depth 8 seldepth 10 multipv 1 score cp 21 nodes 10 nps 1 pv e2e4 e7e5",
            "info depth 8 seldepth 10 multipv 2 score cp 11 nodes 10 nps 1 pv d2d4 d7d5",
            "info depth 12 seldepth 14 multipv 1 score cp 34 nodes 20 nps 2 pv e2e4 c7c5",
            "info depth 12 seldepth 14 multipv 2 score mate 3 nodes 20 nps 2 pv d2d4 g8f6",
        ],
        turn="w",
    )

    assert [line.multipv for line in lines] == [1, 2]
    assert lines[0].score == 34
    assert lines[0].pv == ["e2e4", "c7c5"]
    assert lines[1].score == "mate3"


def test_parse_lc0_info_without_multipv_defaults_to_first_line() -> None:
    lines = parse_stockfish_info_lines(
        [
            "info depth 1 seldepth 2 time 151 nodes 6 score cp 16 nps 42 pv g1f3 d7d5",
            "info depth 3 seldepth 6 time 903 nodes 64 score cp 15 nps 71 pv d2d4 d7d5 g1f3",
        ],
        turn="w",
    )

    assert len(lines) == 1
    assert lines[0].multipv == 1
    assert lines[0].score == 15
    assert lines[0].pv == ["d2d4", "d7d5", "g1f3"]


def test_stockfish_capability_reports_missing_binary() -> None:
    worker = LocalStockfishWorker(binary_path="/definitely/missing/stockfish", max_workers=10)

    capability = worker.capability()

    assert capability.key == "stockfish"
    assert capability.available is False
    assert capability.concurrency_limit == 10
    assert "not found" in capability.detail


def test_alphazero_unavailable_does_not_fallback_to_stockfish() -> None:
    worker = AlphaZeroWorker(max_workers=1, timeout=1)

    with patch("core.chess_engine.local_workers.settings.ALPHAZERO_COMMAND", ""), patch(
        "core.chess_engine.local_workers.settings.ALPHAZERO_MODEL_PATH", ""
    ):
        with pytest.raises(ChessEngineError) as exc:
            worker.analyze(
                fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                depth=10,
                multipv=1,
            )

    assert "AlphaZero unavailable" in str(exc.value)


def test_lc0_capability_reports_missing_runtime() -> None:
    worker = Lc0Worker(binary_path="/definitely/missing/lc0", weights_path="", max_workers=1, timeout=1)

    capability = worker.capability()

    assert capability.key == "lc0"
    assert capability.available is False
    assert capability.concurrency_limit == 1
    assert "Missing" in capability.detail


def test_lc0_unavailable_does_not_fallback_to_stockfish() -> None:
    worker = Lc0Worker(binary_path="/definitely/missing/lc0", weights_path="", max_workers=1, timeout=1)

    with pytest.raises(ChessEngineError) as exc:
        worker.analyze(
            fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            depth=10,
            multipv=1,
        )

    assert "LC0 unavailable" in str(exc.value)


def test_cross_process_slot_limiter_rejects_second_slot_when_full(tmp_path: Path) -> None:
    limiter_a = CrossProcessSlotLimiter("test-engine", limit=1, root=str(tmp_path))
    limiter_b = CrossProcessSlotLimiter("test-engine", limit=1, root=str(tmp_path))

    with limiter_a.acquire(timeout=1):
        with pytest.raises(ChessEngineTimeoutError):
            with limiter_b.acquire(timeout=1):
                pass
