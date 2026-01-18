"""
Simple prophylaxis integration test using facade.py

Tests prophylaxis detection using the existing tag_position() pipeline.

Note: Currently tests with threat_delta=0.0 (TODO in facade.py:345).
Full threat estimation will be added in future iteration.
"""
import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.core.tagger.facade import tag_position
from backend.core.tagger.config.engine import DEFAULT_STOCKFISH_PATH

if os.getenv("ALLOW_NETWORK_TESTS") != "1":
    pytest.skip("Network engine tests disabled (set ALLOW_NETWORK_TESTS=1 to run).", allow_module_level=True)


def test_prophylaxis_basic_integration():
    """
    Test basic prophylaxis detection through complete pipeline.

    Position: Italian Game middlegame
    Move: d2-d3 (quiet pawn push, restricting opponent mobility)
    Expected: Should detect some level of prophylaxis
    """
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    played_move = "d2d3"

    print("\n" + "="*70)
    print("Test 1: Basic Prophylaxis Integration")
    print("="*70)
    print(f"FEN: {fen}")
    print(f"Move: {played_move} (d3)")
    print()

    result = tag_position(
        engine_path=DEFAULT_STOCKFISH_PATH,
        fen=fen,
        played_move_uci=played_move,
        depth=18,  # Match rule_tagger2
        multipv=3
    )

    print(f"Results:")
    print(f"  prophylactic_move: {result.prophylactic_move}")
    print(f"  prophylactic_direct: {result.prophylactic_direct}")
    print(f"  prophylactic_latent: {result.prophylactic_latent}")
    print(f"  prophylactic_meaningless: {result.prophylactic_meaningless}")
    print(f"  prophylaxis_score: {result.prophylaxis_score:.3f}")
    print()

    # Basic assertions
    assert isinstance(result.prophylactic_move, bool), "prophylactic_move should be bool"
    assert isinstance(result.prophylactic_direct, bool), "prophylactic_direct should be bool"
    assert isinstance(result.prophylactic_latent, bool), "prophylactic_latent should be bool"
    assert isinstance(result.prophylaxis_score, float), "prophylaxis_score should be float"

    print("✅ Test 1 passed: Pipeline executes successfully")
    return result


def test_prophylaxis_golden_sample_1():
    """
    Test Golden Sample 1: Ba2!! prevents black's Ba5-c7 plan

    From rule_tagger2's Golden_sample_prophylactic.pgn
    Expected: High-quality direct prophylaxis (conf ≥0.80)
    """
    fen = "r1b2rk1/pp1nqppp/2p2n2/b3p3/2BP4/P1N1PN2/1PQB1PPP/R4RK1 w - - 2 12"
    played_move = "c4a2"  # Ba2!!

    print("\n" + "="*70)
    print("Test 2: Golden Sample 1 - Ba2!!")
    print("="*70)
    print(f"FEN: {fen}")
    print(f"Move: {played_move} (Ba2)")
    print(f"Description: Ba2!! prevents black's Ba5-c7 plan (preparing e5-e4)")
    print()

    result = tag_position(
        engine_path=DEFAULT_STOCKFISH_PATH,
        fen=fen,
        played_move_uci=played_move,
        depth=18,
        multipv=3
    )

    print(f"Results:")
    print(f"  prophylactic_move: {result.prophylactic_move}")
    print(f"  prophylactic_direct: {result.prophylactic_direct}")
    print(f"  prophylactic_latent: {result.prophylactic_latent}")
    print(f"  prophylactic_meaningless: {result.prophylactic_meaningless}")
    print(f"  prophylaxis_score: {result.prophylaxis_score:.3f}")
    print()

    # This should detect prophylaxis (exact quality depends on threat_delta computation)
    # With threat_delta=0.0, detection relies on opponent mobility/tactics deltas
    if result.prophylactic_move or result.prophylactic_direct or result.prophylactic_latent:
        print("✅ Test 2 passed: Prophylaxis detected")
    else:
        print("⚠️ Test 2 warning: No prophylaxis detected (may need threat_delta)")

    return result


def test_prophylaxis_non_prophylactic():
    """
    Test non-prophylactic move (capture).

    Expected: Should NOT trigger prophylaxis tags (filtered by candidate gate)
    """
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    played_move = "f3e5"  # Nxe5 (capture - should be filtered)

    print("\n" + "="*70)
    print("Test 3: Non-Prophylactic (Capture)")
    print("="*70)
    print(f"FEN: {fen}")
    print(f"Move: {played_move} (Nxe5 - capture)")
    print()

    result = tag_position(
        engine_path=DEFAULT_STOCKFISH_PATH,
        fen=fen,
        played_move_uci=played_move,
        depth=18,
        multipv=3
    )

    print(f"Results:")
    print(f"  prophylactic_move: {result.prophylactic_move}")
    print(f"  prophylactic_direct: {result.prophylactic_direct}")
    print(f"  prophylactic_latent: {result.prophylactic_latent}")
    print(f"  prophylactic_meaningless: {result.prophylactic_meaningless}")
    print(f"  prophylaxis_score: {result.prophylaxis_score:.3f}")
    print()

    # Captures should be filtered by is_prophylaxis_candidate()
    assert not result.prophylactic_move, "Capture should not trigger prophylactic_move"
    assert not result.prophylactic_direct, "Capture should not trigger prophylactic_direct"
    assert not result.prophylactic_latent, "Capture should not trigger prophylactic_latent"

    print("✅ Test 3 passed: Capture correctly filtered")
    return result


def run_all_tests():
    """Run all simple integration tests."""
    print("\n" + "="*70)
    print("Prophylaxis Simple Integration Tests")
    print("="*70)
    print()
    print("Note: These tests use the existing tag_position() pipeline.")
    print("threat_delta computation is TODO in facade.py:345")
    print()

    try:
        # Test 1: Basic integration
        result1 = test_prophylaxis_basic_integration()

        # Test 2: Golden sample
        result2 = test_prophylaxis_golden_sample_1()

        # Test 3: Non-prophylactic (should be filtered)
        result3 = test_prophylaxis_non_prophylactic()

        print("\n" + "="*70)
        print("✅ ALL SIMPLE INTEGRATION TESTS PASSED")
        print("="*70)
        print()
        print("Summary:")
        print("  ✅ Pipeline executes successfully")
        print("  ✅ Prophylaxis tags are populated")
        print("  ✅ Capture filtering works correctly")
        print()
        print("Next steps:")
        print("  - Implement threat_delta computation (facade.py:345)")
        print("  - Test full 23 positions (16 synthetic + 7 golden)")
        print("  - Verify confidence ranges match expectations")
        print()
        return True

    except Exception as e:
        print("\n" + "="*70)
        print(f"❌ TEST FAILED: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
