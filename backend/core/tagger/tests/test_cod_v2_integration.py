"""
Integration tests for CoD v2 detection.
Tests the full pipeline from position to tag detection.
"""
import sys
from pathlib import Path

# Add backend directory to path for package imports
backend_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(backend_root))

try:
    from core.tagger import facade
    tag_position = facade.tag_position
    print("✓ Successfully imported tag_position from facade")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    print(f"  backend_root: {backend_root}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# Test positions designed to trigger each CoD v2 subtype
TEST_POSITIONS = [
    {
        "name": "Prophylaxis - Preventing knight jump",
        "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        "move": "d2d3",  # Prevents Nd4
        "expected_subtype": "prophylaxis",
        "expected_tags": ["control_over_dynamics", "cod_prophylaxis"],
    },
    {
        "name": "Piece Control - Knight outpost",
        "fen": "r1bqkb1r/ppp2ppp/2np1n2/4p3/2BPP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
        "move": "c3d5",  # Knight to d5 controls key squares
        "expected_subtype": "piece_control",
        "expected_tags": ["control_over_dynamics", "piece_control_over_dynamics"],
    },
    {
        "name": "Pawn Control - Space restriction",
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "move": "e2e4",  # Central pawn advance
        "expected_subtype": "pawn_control",
        "expected_tags": ["control_over_dynamics", "pawn_control_over_dynamics"],
    },
    {
        "name": "Simplification - Exchange when ahead",
        "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 5",
        "move": "c4f7",  # Bishop takes f7, simplifying
        "expected_subtype": "simplification",
        "expected_tags": ["control_over_dynamics", "control_simplification"],
    },
]


def run_test(position, engine_path="/usr/games/stockfish"):
    """Run a single test position."""
    print(f"\n{'='*60}")
    print(f"Test: {position['name']}")
    print(f"FEN: {position['fen']}")
    print(f"Move: {position['move']}")
    print(f"Expected: {position['expected_subtype']}")
    print(f"{'='*60}")

    try:
        result = tag_position(
            engine_path=engine_path,
            fen=position["fen"],
            played_move_uci=position["move"],
        )

        # Check CoD detection
        print(f"\nResults:")
        print(f"  control_over_dynamics: {result.control_over_dynamics}")
        print(f"  control_over_dynamics_subtype: {result.control_over_dynamics_subtype}")

        # Check subtype boolean tags
        print(f"\nSubtype tags:")
        print(f"  cod_prophylaxis: {result.cod_prophylaxis}")
        print(f"  piece_control_over_dynamics: {result.piece_control_over_dynamics}")
        print(f"  pawn_control_over_dynamics: {result.pawn_control_over_dynamics}")
        print(f"  control_simplification: {result.control_simplification}")

        # Check diagnostics
        if "cod_v2" in result.analysis_context.get("engine_meta", {}):
            cod_diag = result.analysis_context["engine_meta"]["cod_v2"]
            print(f"\nDiagnostics:")
            print(f"  detected: {cod_diag.get('detected', False)}")
            print(f"  subtype: {cod_diag.get('subtype', 'N/A')}")
            print(f"  gates_passed: {cod_diag.get('gates_passed', {})}")

        # Validation
        success = True
        if result.control_over_dynamics:
            actual_subtype = result.control_over_dynamics_subtype
            expected_subtype = position["expected_subtype"]

            if actual_subtype == expected_subtype:
                print(f"\n✓ PASS: Detected expected subtype '{expected_subtype}'")
            else:
                print(f"\n✗ FAIL: Expected '{expected_subtype}', got '{actual_subtype}'")
                success = False

            # Check boolean tag
            tag_map = {
                "prophylaxis": result.cod_prophylaxis,
                "piece_control": result.piece_control_over_dynamics,
                "pawn_control": result.pawn_control_over_dynamics,
                "simplification": result.control_simplification,
            }
            if tag_map.get(expected_subtype, False):
                print(f"✓ Boolean tag correctly set")
            else:
                print(f"✗ Boolean tag not set correctly")
                success = False
        else:
            print(f"\n✗ FAIL: No CoD detected (expected '{position['expected_subtype']}')")
            success = False

        return success

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("CoD v2 Integration Tests")
    print("="*60)

    # Check for Stockfish
    import os
    stockfish_paths = [
        "/usr/games/stockfish",
        "/usr/local/bin/stockfish",
        "/usr/bin/stockfish",
    ]

    engine_path = None
    for path in stockfish_paths:
        if os.path.exists(path):
            engine_path = path
            print(f"✓ Found Stockfish at: {engine_path}")
            break

    if not engine_path:
        print("✗ Stockfish not found. Please install Stockfish:")
        print("  sudo apt-get install stockfish")
        return

    # Run tests
    results = []
    for position in TEST_POSITIONS:
        success = run_test(position, engine_path)
        results.append((position["name"], success))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
