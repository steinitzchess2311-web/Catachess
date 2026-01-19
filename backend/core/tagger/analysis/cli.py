#!/usr/bin/env python3
"""
Command-line interface for PGN tag analysis pipeline.

Usage:
    python -m backend.core.tagger.analysis.cli input.pgn
    python -m backend.core.tagger.analysis.cli input.pgn --output-dir custom_output
    python -m backend.core.tagger.analysis.cli input.pgn --max-positions 100
    python -m backend.core.tagger.analysis.cli input.pgn --engine-mode http
"""

import argparse
import os
import sys
from pathlib import Path

from .pipeline import AnalysisPipeline
from ..config.engine import DEFAULT_DEPTH, DEFAULT_MULTIPV, DEFAULT_STOCKFISH_PATH

DEFAULT_ENGINE_URL = os.environ.get("ENGINE_URL", "https://sf.catachess.com/engine")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze PGN files and calculate tag occurrence percentages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "pgn_file",
        type=str,
        help="Path to input PGN file"
    )

    # Optional arguments
    parser.add_argument(
        "--output-dir",
        type=str,
        default="backend/core/tagger/data/output",
        help="Output directory for results (default: backend/core/tagger/data/output)"
    )

    parser.add_argument(
        "--engine-mode",
        type=str,
        choices=["local", "http"],
        default="http",
        help="Engine mode: 'local' for local Stockfish, 'http' for remote service (default: http)"
    )

    parser.add_argument(
        "--engine-path",
        type=str,
        default=DEFAULT_STOCKFISH_PATH,
        help=f"Path to Stockfish engine for local mode (default: {DEFAULT_STOCKFISH_PATH})"
    )

    parser.add_argument(
        "--engine-url",
        type=str,
        default=DEFAULT_ENGINE_URL,
        help=f"Remote engine URL for http mode (default: {DEFAULT_ENGINE_URL})"
    )

    parser.add_argument(
        "--depth",
        type=int,
        default=DEFAULT_DEPTH,
        help=f"Engine analysis depth (default: {DEFAULT_DEPTH})"
    )

    parser.add_argument(
        "--multipv",
        type=int,
        default=DEFAULT_MULTIPV,
        help=f"Number of principal variations (default: {DEFAULT_MULTIPV})"
    )

    parser.add_argument(
        "--skip-opening-moves",
        type=int,
        default=0,
        help="Number of opening moves to skip (default: 0)"
    )

    parser.add_argument(
        "--max-positions",
        type=int,
        default=None,
        help="Maximum number of positions to analyze (default: all)"
    )

    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Don't save JSON output"
    )

    parser.add_argument(
        "--no-txt",
        action="store_true",
        help="Don't save text report"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    # Validate input file
    pgn_path = Path(args.pgn_file)
    if not pgn_path.exists():
        print(f"Error: PGN file not found: {pgn_path}", file=sys.stderr)
        sys.exit(1)

    # Check if local engine exists (only in local mode)
    if args.engine_mode == "local":
        engine_path = Path(args.engine_path)
        if not engine_path.exists():
            print(f"Error: Stockfish engine not found: {engine_path}", file=sys.stderr)
            print(f"Please install stockfish or specify path with --engine-path", file=sys.stderr)
            print(f"Or use --engine-mode http to use remote engine", file=sys.stderr)
            sys.exit(1)

    # Create pipeline
    pipeline = AnalysisPipeline(
        pgn_path=pgn_path,
        output_dir=args.output_dir,
        engine_path=args.engine_path,
        engine_url=args.engine_url,
        engine_mode=args.engine_mode,
        depth=args.depth,
        multipv=args.multipv,
        skip_opening_moves=args.skip_opening_moves,
    )

    # Run analysis
    try:
        stats = pipeline.run_and_save(
            verbose=not args.quiet,
            max_positions=args.max_positions,
            save_json=not args.no_json,
            save_txt=not args.no_txt,
        )

        # Print summary
        if not args.quiet:
            print()
            print("=" * 80)
            print(f"Analysis complete!")
            print(f"Total positions analyzed: {stats.total_positions}")
            print(f"Unique tags found: {len(stats.tag_counts)}")
            print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError during analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
