#!/usr/bin/env python3
"""
Example usage of the chess tagger system.
Run this script to see the tagger in action.

Usage:
    python3 -m backend.modules.tagger_core.example_usage
"""

import sys
from pathlib import Path

# Add catachess to path if running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.modules.tagger_core.facade import tag_position


def example_good_opening_move():
    """Example 1: Tag a good opening move (e2e4)."""
    print("=" * 60)
    print("Example 1: Good Opening Move (e2e4)")
    print("=" * 60)

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    move = "e2e4"

    result = tag_position(
        engine_path=None,  # Use default stockfish
        fen=fen,
        played_move_uci=move,
        depth=12,
        multipv=5,
    )

    print(f"Position: Starting position")
    print(f"Played move: {result.played_move} ({result.played_kind})")
    print(f"Best move: {result.best_move} ({result.best_kind})")
    print(f"\nEvaluations:")
    print(f"  Before: {result.eval_before:+.2f}")
    print(f"  Played: {result.eval_played:+.2f}")
    print(f"  Best: {result.eval_best:+.2f}")
    print(f"  Delta: {result.delta_eval:+.2f}")
    print(f"\nTags:")
    print(f"  First Choice: {result.first_choice}")
    print(f"  Mode: {result.mode}")
    print()


def example_tactical_position():
    """Example 2: Tag a move in a tactical position."""
    print("=" * 60)
    print("Example 2: Tactical Position")
    print("=" * 60)

    # Italian Game with hanging bishop on c4
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    move = "g8f6"  # Develops knight

    result = tag_position(
        engine_path=None,
        fen=fen,
        played_move_uci=move,
        depth=12,
        multipv=5,
    )

    print(f"Position: Italian Game")
    print(f"Played move: {result.played_move} ({result.played_kind})")
    print(f"Best move: {result.best_move} ({result.best_kind})")
    print(f"\nEvaluations:")
    print(f"  Before: {result.eval_before:+.2f}")
    print(f"  Played: {result.eval_played:+.2f}")
    print(f"  Best: {result.eval_best:+.2f}")
    print(f"  Delta: {result.delta_eval:+.2f}")
    print(f"\nTags:")
    print(f"  First Choice: {result.first_choice}")
    print(f"  Mode: {result.mode}")
    print()


def example_blunder():
    """Example 3: Tag a blunder."""
    print("=" * 60)
    print("Example 3: Blunder Detection")
    print("=" * 60)

    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    move = "f2f3"  # Weakening move

    result = tag_position(
        engine_path=None,
        fen=fen,
        played_move_uci=move,
        depth=12,
        multipv=5,
    )

    print(f"Position: Starting position")
    print(f"Played move: {result.played_move} ({result.played_kind})")
    print(f"Best move: {result.best_move} ({result.best_kind})")
    print(f"\nEvaluations:")
    print(f"  Before: {result.eval_before:+.2f}")
    print(f"  Played: {result.eval_played:+.2f}")
    print(f"  Best: {result.eval_best:+.2f}")
    print(f"  Delta: {result.delta_eval:+.2f} (negative = worse)")
    print(f"\nTags:")
    print(f"  First Choice: {result.first_choice} (should be False)")
    print(f"  Mode: {result.mode}")
    print()


def example_endgame():
    """Example 4: Tag an endgame move."""
    print("=" * 60)
    print("Example 4: Endgame Position")
    print("=" * 60)

    # King and pawn endgame
    fen = "8/5k2/8/8/3K4/8/4P3/8 w - - 0 1"
    move = "e2e4"  # Push the pawn

    result = tag_position(
        engine_path=None,
        fen=fen,
        played_move_uci=move,
        depth=15,  # Higher depth for endgame
        multipv=3,
    )

    print(f"Position: King and pawn endgame")
    print(f"Played move: {result.played_move} ({result.played_kind})")
    print(f"Best move: {result.best_move} ({result.best_kind})")
    print(f"\nEvaluations:")
    print(f"  Before: {result.eval_before:+.2f}")
    print(f"  Played: {result.eval_played:+.2f}")
    print(f"  Best: {result.eval_best:+.2f}")
    print(f"  Delta: {result.delta_eval:+.2f}")
    print(f"\nTags:")
    print(f"  First Choice: {result.first_choice}")
    print(f"  Mode: {result.mode}")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Chess Tagger System - Example Usage".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    try:
        example_good_opening_move()
        example_tactical_position()
        example_blunder()
        example_endgame()

        print("=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        print()
        print("Note: Currently only 'first_choice' tag is implemented.")
        print("See NEXT_STEPS.md for how to add more tags.")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
