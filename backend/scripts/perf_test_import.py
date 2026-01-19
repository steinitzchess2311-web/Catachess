#!/usr/bin/env python
"""
Performance test for PGN import - measures single chapter import time.

Usage:
    PYTHONPATH=.:backend python backend/scripts/perf_test_import.py
"""

import asyncio
import os
import sys
import time
import tracemalloc
from pathlib import Path

# Setup Django-style settings loading
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.core.config import settings
from core.new_pgn import PGNGame, detect_games
from backend.core.real_pgn.parser import parse_pgn
from backend.core.real_pgn.builder import build_pgn
from backend.core.real_pgn.fen import build_fen_index

# Test PGN (simple 10-move game)
SIMPLE_PGN = """[Event "Test"]
[Site "Local"]
[Date "2026.01.18"]
[Round "1"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 *
"""

# Medium complexity PGN with variations
MEDIUM_PGN = """[Event "Test Medium"]
[Site "Local"]
[Date "2026.01.18"]
[Round "1"]
[White "White"]
[Black "Black"]
[Result "*"]

1. e4 e5 (1... c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4) 2. Nf3 Nc6 (2... Nf6 3. Nxe5 d6 4. Nf3 Nxe4) 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 *
"""


async def test_parse_performance():
    """Test PGN parsing performance."""
    print("=" * 60)
    print("PGN Parse Performance Test")
    print("=" * 60)

    # Test simple PGN
    tracemalloc.start()
    start = time.perf_counter()

    iterations = 100
    for _ in range(iterations):
        tree = parse_pgn(SIMPLE_PGN)

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    per_parse = (elapsed / iterations) * 1000  # ms
    print(f"\nSimple PGN (10 moves):")
    print(f"  Total time for {iterations} parses: {elapsed:.3f}s")
    print(f"  Per-parse: {per_parse:.2f}ms")
    print(f"  Memory: current={current/1024:.1f}KB, peak={peak/1024:.1f}KB")

    # Test medium PGN with variations
    tracemalloc.start()
    start = time.perf_counter()

    for _ in range(iterations):
        tree = parse_pgn(MEDIUM_PGN)

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    per_parse = (elapsed / iterations) * 1000
    print(f"\nMedium PGN (with variations):")
    print(f"  Total time for {iterations} parses: {elapsed:.3f}s")
    print(f"  Per-parse: {per_parse:.2f}ms")
    print(f"  Memory: current={current/1024:.1f}KB, peak={peak/1024:.1f}KB")

    return per_parse


async def test_fen_index_performance():
    """Test FEN index building performance."""
    print("\n" + "=" * 60)
    print("FEN Index Build Performance Test")
    print("=" * 60)

    tree = parse_pgn(MEDIUM_PGN)

    tracemalloc.start()
    start = time.perf_counter()

    iterations = 100
    for _ in range(iterations):
        fen_index = build_fen_index(tree)

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    per_build = (elapsed / iterations) * 1000
    print(f"\nFEN index build (medium tree):")
    print(f"  Total time for {iterations} builds: {elapsed:.3f}s")
    print(f"  Per-build: {per_build:.2f}ms")
    print(f"  Index entries: {len(fen_index)}")
    print(f"  Memory: current={current/1024:.1f}KB, peak={peak/1024:.1f}KB")

    return per_build, len(fen_index)


async def test_large_pgn_sample():
    """Test with sample from large PGN file."""
    print("\n" + "=" * 60)
    print("Large PGN Sample Test")
    print("=" * 60)

    pgn_path = Path("docs/performance_reports/large_pgn_generated.pgn")
    if not pgn_path.exists():
        print("  Large PGN file not found, skipping")
        return None, None

    # Read first few games
    content = pgn_path.read_text()
    games = detect_games(content)

    print(f"  Total games in file: {len(games)}")

    # Test parsing first 10 games
    sample_games = games[:10]

    tracemalloc.start()
    start = time.perf_counter()

    total_nodes = 0
    for game in sample_games:
        tree = parse_pgn(game.raw)
        total_nodes += len(tree.nodes)

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    per_game = (elapsed / len(sample_games)) * 1000
    print(f"\n  Parsed {len(sample_games)} games:")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Per-game: {per_game:.2f}ms")
    print(f"  Total nodes: {total_nodes}")
    print(f"  Memory: current={current/1024:.1f}KB, peak={peak/1024/1024:.1f}MB")

    # Estimate full import time
    estimated_total = (per_game / 1000) * len(games)
    print(f"\n  Estimated full import ({len(games)} games): {estimated_total:.1f}s")

    return per_game, estimated_total


async def main():
    """Run all performance tests."""
    print("\n" + "=" * 60)
    print("Stage 3C Performance Validation")
    print("=" * 60)

    parse_time = await test_parse_performance()
    fen_time, fen_count = await test_fen_index_performance()
    per_game, estimated = await test_large_pgn_sample()

    print("\n" + "=" * 60)
    print("SUMMARY - Threshold Check")
    print("=" * 60)

    # Threshold: Import single chapter < 2s
    # Note: This is parse only, not full DB+R2 write
    print(f"\n1. Import (parse only):")
    print(f"   Target: < 2000ms per chapter")
    if per_game:
        print(f"   Actual: {per_game:.2f}ms per chapter (parse only)")
        if per_game < 2000:
            print(f"   Status: PASS (parse phase)")
        else:
            print(f"   Status: FAIL")

    # Threshold: FEN index build
    print(f"\n2. FEN index build:")
    print(f"   Actual: {fen_time:.2f}ms per build")
    print(f"   Entries per build: {fen_count}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
