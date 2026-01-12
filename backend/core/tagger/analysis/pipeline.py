"""
Main analysis pipeline for processing PGN files and calculating tag statistics.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config.engine import DEFAULT_DEPTH, DEFAULT_MULTIPV, DEFAULT_STOCKFISH_PATH
from ..facade import tag_position
from .pgn_processor import PGNProcessor
from .tag_statistics import TagStatistics


class AnalysisPipeline:
    """
    Pipeline for analyzing PGN files and calculating tag statistics.

    Usage:
        pipeline = AnalysisPipeline(
            pgn_path="data/pgn/games.pgn",
            output_dir="data/output"
        )
        stats = pipeline.run()
    """

    def __init__(
        self,
        pgn_path: str | Path,
        output_dir: str | Path,
        engine_path: Optional[str] = None,
        depth: int = DEFAULT_DEPTH,
        multipv: int = DEFAULT_MULTIPV,
        skip_opening_moves: int = 0,
    ):
        """
        Initialize analysis pipeline.

        Args:
            pgn_path: Path to input PGN file
            output_dir: Directory for output files
            engine_path: Path to Stockfish engine (default: /usr/games/stockfish)
            depth: Engine analysis depth (default: 14)
            multipv: Number of principal variations (default: 6)
            skip_opening_moves: Number of opening moves to skip (default: 0)
        """
        self.pgn_path = Path(pgn_path)
        self.output_dir = Path(output_dir)
        self.engine_path = engine_path or DEFAULT_STOCKFISH_PATH
        self.depth = depth
        self.multipv = multipv
        self.skip_opening_moves = skip_opening_moves

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, verbose: bool = True, max_positions: Optional[int] = None) -> TagStatistics:
        """
        Run the analysis pipeline.

        Args:
            verbose: Print progress messages (default: True)
            max_positions: Maximum positions to analyze (default: None = all)

        Returns:
            TagStatistics with collected data
        """
        if verbose:
            print(f"Starting analysis of {self.pgn_path}")
            print(f"Engine: {self.engine_path}")
            print(f"Depth: {self.depth}, MultiPV: {self.multipv}")
            print(f"Skip opening moves: {self.skip_opening_moves}")
            print()

        # Initialize processor and statistics
        processor = PGNProcessor(self.pgn_path)
        stats = TagStatistics()

        # Count total games
        if verbose:
            num_games = processor.count_games()
            print(f"Total games in PGN: {num_games}")
            print("Processing positions...")
            print()

        # Process each position
        position_count = 0
        error_count = 0

        for position in processor.extract_positions(skip_opening_moves=self.skip_opening_moves):
            # Check max positions limit
            if max_positions and position_count >= max_positions:
                if verbose:
                    print(f"\nReached max_positions limit ({max_positions})")
                break

            position_count += 1

            # Progress update
            if verbose and position_count % 10 == 0:
                print(f"Processed {position_count} positions...", end="\r")

            try:
                # Run tagging pipeline
                result = tag_position(
                    engine_path=self.engine_path,
                    fen=position.fen,
                    played_move_uci=position.played_move_uci,
                    depth=self.depth,
                    multipv=self.multipv,
                )

                # Add to statistics
                stats.add_result(result)

            except Exception as e:
                error_count += 1
                if verbose:
                    print(f"\nError at position {position_count} "
                          f"(Game {position.game_index}, Move {position.move_number}): {e}")

        if verbose:
            print(f"\nCompleted: {position_count} positions processed")
            if error_count > 0:
                print(f"Errors encountered: {error_count}")
            print()

        return stats

    def run_and_save(
        self,
        verbose: bool = True,
        max_positions: Optional[int] = None,
        save_json: bool = True,
        save_txt: bool = True,
    ) -> TagStatistics:
        """
        Run analysis and save results to files.

        Args:
            verbose: Print progress messages
            max_positions: Maximum positions to analyze
            save_json: Save results as JSON
            save_txt: Save results as text report

        Returns:
            TagStatistics with collected data
        """
        # Run analysis
        stats = self.run(verbose=verbose, max_positions=max_positions)

        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = self.pgn_path.stem

        # Save text report
        if save_txt:
            txt_path = self.output_dir / f"{base_name}_stats_{timestamp}.txt"
            with open(txt_path, 'w') as f:
                f.write(stats.format_report())
            if verbose:
                print(f"Text report saved to: {txt_path}")

        # Save JSON data
        if save_json:
            json_path = self.output_dir / f"{base_name}_stats_{timestamp}.json"
            json_data = {
                "metadata": {
                    "pgn_file": str(self.pgn_path),
                    "timestamp": timestamp,
                    "total_positions": stats.total_positions,
                    "depth": self.depth,
                    "multipv": self.multipv,
                    "skip_opening_moves": self.skip_opening_moves,
                },
                "tag_counts": dict(stats.tag_counts),
                "tag_percentages": stats.get_percentages(),
            }
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            if verbose:
                print(f"JSON data saved to: {json_path}")

        return stats


__all__ = ["AnalysisPipeline"]
