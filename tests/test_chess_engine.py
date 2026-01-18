import os
import sys
from pathlib import Path

import pytest

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from core.chess_engine.client import EngineClient

if os.getenv("ALLOW_NETWORK_TESTS") != "1":
    pytest.skip("Network engine tests disabled (set ALLOW_NETWORK_TESTS=1 to run).", allow_module_level=True)


def test_engine_analyze():
    engine = EngineClient()  # ← 不传 URL，自动用 config
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    result = engine.analyze(fen, depth=15, multipv=3)

    assert result.lines
