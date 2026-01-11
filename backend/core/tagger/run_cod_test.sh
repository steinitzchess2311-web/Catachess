#!/bin/bash
# Run CoD v2 integration test with proper environment

cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Activated virtual environment"
else
    echo "✗ Virtual environment not found"
    echo "  Run: python3 -m venv venv && source venv/bin/activate && pip install python-chess"
    exit 1
fi

# Change to backend directory for proper package imports
cd ../../..

# Run test using Python module syntax
export PYTHONPATH="$(pwd):$PYTHONPATH"
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/catadragon/Code/catachess/backend')

from core.tagger import tag_position
import os

print("="*60)
print("CoD v2 Boolean Tag Mapping Test")
print("="*60)

# Find Stockfish
stockfish_paths = [
    "/usr/games/stockfish",
    "/usr/local/bin/stockfish",
    "/usr/bin/stockfish",
]

engine_path = None
for path in stockfish_paths:
    if os.path.exists(path):
        engine_path = path
        print(f"✓ Stockfish found: {engine_path}\n")
        break

if not engine_path:
    print("✗ Stockfish not found")
    sys.exit(1)

# Test position
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
move = "e2e4"

print(f"Position: {fen}")
print(f"Move: {move}\n")

try:
    result = tag_position(
        engine_path=engine_path,
        fen=fen,
        played_move_uci=move,
    )

    print("CoD v2 Detection:")
    print(f"  control_over_dynamics: {result.control_over_dynamics}")
    print(f"  subtype: {result.control_over_dynamics_subtype}")

    print("\nCoD v2 Boolean Tags:")
    print(f"  cod_prophylaxis: {result.cod_prophylaxis}")
    print(f"  piece_control_over_dynamics: {result.piece_control_over_dynamics}")
    print(f"  pawn_control_over_dynamics: {result.pawn_control_over_dynamics}")
    print(f"  control_simplification: {result.control_simplification}")

    print("\nLegacy Tags (should be False):")
    print(f"  cod_simplify: {result.cod_simplify}")
    print(f"  cod_plan_kill: {result.cod_plan_kill}")

    # Validation
    print("\n" + "="*60)
    print("Validation:")

    if result.control_over_dynamics:
        # Count set tags
        tags_set = sum([
            result.cod_prophylaxis,
            result.piece_control_over_dynamics,
            result.pawn_control_over_dynamics,
            result.control_simplification,
        ])

        if tags_set == 1:
            print("✓ Exactly one CoD v2 boolean tag set")
        else:
            print(f"✗ Expected 1 tag, got {tags_set}")

        # Check mapping
        mapping = {
            "prophylaxis": result.cod_prophylaxis,
            "piece_control": result.piece_control_over_dynamics,
            "pawn_control": result.pawn_control_over_dynamics,
            "simplification": result.control_simplification,
        }

        if mapping.get(result.control_over_dynamics_subtype):
            print(f"✓ Subtype '{result.control_over_dynamics_subtype}' correctly mapped")
        else:
            print(f"✗ Subtype mapping failed")
    else:
        print("ℹ No CoD detected (may be expected)")

    # Check legacy tags
    legacy_count = sum([
        result.cod_simplify, result.cod_plan_kill, result.cod_freeze_bind,
        result.cod_blockade_passed, result.cod_file_seal, result.cod_king_safety_shell,
        result.cod_space_clamp, result.cod_regroup_consolidate, result.cod_slowdown,
    ])

    if legacy_count == 0:
        print("✓ All legacy tags False")
    else:
        print(f"✗ {legacy_count} legacy tags set")

    print("="*60)
    print("✓ Test completed")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
