"""
Main analysis pipeline for processing PGN files and calculating tag statistics.

Supports two input modes:
1. PGN file processing (legacy)
2. FEN index processing (v2 - preferred for NodeTree-based chapters)

Performance targets:
- 100+ nodes in < 5s (batch mode)
- Per-node timeout: 50ms average (with engine call)
- Graceful degradation on failures (record error, continue processing)
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

from modules.workspace.pgn_v2.repo import PgnV2Repo # Import PgnV2Repo
from ..config.engine import DEFAULT_DEPTH, DEFAULT_MULTIPV, DEFAULT_STOCKFISH_PATH
from ..facade import tag_position
from .pgn_processor import PGNProcessor
from .tag_statistics import TagStatistics
from .fen_processor import FenIndexProcessor, NodeFenEntry
from ..pipeline.predictor.node_predictor import NodePredictor, NodeTagResult

logger = logging.getLogger(__name__)

# Default HTTP engine URL
DEFAULT_ENGINE_URL = os.environ.get("ENGINE_URL", "https://sf.cloudflare.com")


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
        engine_url: Optional[str] = None,
        engine_mode: Literal["local", "http"] = "http",
        depth: int = DEFAULT_DEPTH,
        multipv: int = DEFAULT_MULTIPV,
        skip_opening_moves: int = 0,
        pgn_v2_repo: Optional[PgnV2Repo] = None, # New parameter
    ):
        """
        Initialize analysis pipeline.

        Args:
            pgn_path: Path to input PGN file
            output_dir: Directory for output files
            engine_path: Path to Stockfish engine (for local mode)
            engine_url: Remote engine URL (for http mode)
            engine_mode: "local" for local Stockfish, "http" for remote service
            depth: Engine analysis depth (default: 14)
            multipv: Number of principal variations (default: 6)
            skip_opening_moves: Number of opening moves to skip (default: 0)
            pgn_v2_repo: Optional PgnV2Repo instance for saving v2 PGN data
        """
        self.pgn_path = Path(pgn_path)
        self.output_dir = Path(output_dir)
        self.engine_path = engine_path or DEFAULT_STOCKFISH_PATH
        self.engine_url = engine_url or DEFAULT_ENGINE_URL
        self.engine_mode = engine_mode
        self.depth = depth
        self.multipv = multipv
        self.skip_opening_moves = skip_opening_moves
        self.pgn_v2_repo = pgn_v2_repo # Store the PgnV2Repo instance

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
            if self.engine_mode == "http":
                print(f"Engine: {self.engine_url} (HTTP)")
            else:
                print(f"Engine: {self.engine_path} (local)")
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
                    engine_mode=self.engine_mode,
                    engine_url=self.engine_url,
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

    # Performance thresholds for batch processing
    BATCH_TIMEOUT_SECONDS = 30.0  # Max total time for batch (fail-fast after this)
    PER_NODE_TIMEOUT_MS = 50.0    # Target: 50ms per node for 100 nodes in 5s
    MAX_CONSECUTIVE_ERRORS = 5    # Switch to degraded mode after this many errors

    def run_fen_index(
        self,
        fen_index: Dict[str, str],
        tree_data: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
        max_positions: Optional[int] = None,
        batch_timeout: Optional[float] = None,
    ) -> List[NodeTagResult]:
        """
        Run analysis using FEN index data (v2 mode).

        This is the preferred method for NodeTree-based chapters.
        Uses FenIndexProcessor to extract positions and NodePredictor for tagging.

        Performance optimizations:
        - Batch timeout: Stops engine calls after timeout, records remaining as errors
        - Graceful degradation: After consecutive errors, skips engine calls
        - Per-node tracking: Logs slow nodes for debugging

        Args:
            fen_index: Dict mapping node_id to FEN string
            tree_data: Optional tree JSON with UCI moves for more accurate analysis
            verbose: Print progress messages
            max_positions: Maximum positions to analyze
            batch_timeout: Max seconds for entire batch (default: 30s)

        Returns:
            List of NodeTagResult with tags for each node
        """
        batch_timeout = batch_timeout or self.BATCH_TIMEOUT_SECONDS
        start_time = time.time()

        if verbose:
            logger.info(f"Starting FEN index analysis (timeout={batch_timeout}s)")
            if self.engine_mode == "http":
                logger.info(f"Engine: {self.engine_url} (HTTP)")
            else:
                logger.info(f"Engine: {self.engine_path} (local)")
            logger.info(f"Depth: {self.depth}, MultiPV: {self.multipv}")

        # Process FEN index
        processor = FenIndexProcessor()

        if tree_data:
            # Use tree data for more complete analysis (includes UCI moves)
            entries = processor.process_tree_with_moves(tree_data)
        else:
            # Use basic FEN index
            entries = processor.process_fen_index(fen_index)

        if verbose:
            logger.info(f"Total positions in FEN index: {len(entries)}")

        # Apply max_positions limit
        if max_positions and len(entries) > max_positions:
            entries = entries[:max_positions]
            if verbose:
                logger.info(f"Limited to {max_positions} positions")

        # Performance tracking
        results: List[NodeTagResult] = []
        error_count = 0
        timeout_count = 0
        consecutive_errors = 0
        degraded_mode = False
        slow_nodes = []  # Nodes that took > 2x target time

        for i, entry in enumerate(entries):
            elapsed = time.time() - start_time
            node_start = time.time()

            # Check batch timeout
            if elapsed > batch_timeout:
                if verbose:
                    logger.warning(
                        f"Batch timeout reached ({elapsed:.1f}s > {batch_timeout}s). "
                        f"Processed {i}/{len(entries)} nodes, skipping remaining."
                    )
                # Record remaining as timeout errors
                for remaining_entry in entries[i:]:
                    timeout_count += 1
                    results.append(NodeTagResult(
                        node_id=remaining_entry.node_id,
                        fen=remaining_entry.fen,
                        move_uci=remaining_entry.uci,
                        error="batch_timeout",
                    ))
                break

            if verbose and (i + 1) % 10 == 0:
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.debug(f"Processed {i + 1}/{len(entries)} positions ({rate:.1f}/s)...")

            try:
                if entry.uci and not degraded_mode:
                    result = tag_position(
                        engine_path=self.engine_path,
                        fen=entry.fen,
                        played_move_uci=entry.uci,
                        depth=self.depth,
                        multipv=self.multipv,
                        engine_mode=self.engine_mode,
                        engine_url=self.engine_url,
                    )

                    results.append(NodeTagResult(
                        node_id=entry.node_id,
                        fen=entry.fen,
                        move_uci=entry.uci,
                        tags=list(result.tags) if result.tags else [],
                        features=dict(result.features) if result.features else {},
                    ))
                    consecutive_errors = 0  # Reset on success

                    # Track slow nodes
                    node_time_ms = (time.time() - node_start) * 1000
                    if node_time_ms > self.PER_NODE_TIMEOUT_MS * 2:
                        slow_nodes.append((entry.node_id, node_time_ms))

                elif degraded_mode:
                    # Degraded mode: skip engine calls, record as degraded
                    results.append(NodeTagResult(
                        node_id=entry.node_id,
                        fen=entry.fen,
                        move_uci=entry.uci,
                        error="degraded_mode",
                    ))
                else:
                    # No UCI move - can't analyze
                    results.append(NodeTagResult(
                        node_id=entry.node_id,
                        fen=entry.fen,
                        move_uci=None,
                        tags=[],
                        features={},
                    ))

            except Exception as e:
                error_count += 1
                consecutive_errors += 1
                logger.warning(f"Error analyzing node {entry.node_id}: {e}")
                results.append(NodeTagResult(
                    node_id=entry.node_id,
                    fen=entry.fen,
                    move_uci=entry.uci,
                    error=str(e),
                ))

                # Switch to degraded mode after consecutive errors
                if consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS and not degraded_mode:
                    degraded_mode = True
                    logger.warning(
                        f"Switching to degraded mode after {consecutive_errors} consecutive errors"
                    )

        total_time = time.time() - start_time
        if verbose:
            success_count = len(entries) - error_count - timeout_count
            rate = len(entries) / total_time if total_time > 0 else 0
            logger.info(
                f"Completed: {len(results)} nodes in {total_time:.2f}s ({rate:.1f} nodes/s). "
                f"Success={success_count}, Errors={error_count}, Timeouts={timeout_count}"
            )
            if slow_nodes:
                logger.warning(f"Slow nodes (>{self.PER_NODE_TIMEOUT_MS*2:.0f}ms): {len(slow_nodes)}")
            if degraded_mode:
                logger.warning("Ran in degraded mode - some nodes skipped engine analysis")

        return results

    def run_fen_index_file(
        self,
        fen_index_path: str | Path,
        verbose: bool = True,
        max_positions: Optional[int] = None,
    ) -> List[NodeTagResult]:
        """
        Run analysis using a fen_index.json file (v2 mode).

        Args:
            fen_index_path: Path to fen_index.json
            verbose: Print progress messages
            max_positions: Maximum positions to analyze

        Returns:
            List of NodeTagResult with tags for each node
        """
        processor = FenIndexProcessor()
        fen_index = json.loads(Path(fen_index_path).read_text(encoding="utf-8"))

        if verbose:
            logger.info(f"Starting FEN index analysis from file: {fen_index_path}")

        return self.run_fen_index(
            fen_index=fen_index,
            tree_data=None,
            verbose=verbose,
            max_positions=max_positions,
        )

    def run_fen_index_and_save(
        self,
        fen_index: Dict[str, str],
        chapter_id: str,
        tree_data: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
        max_positions: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run FEN index analysis and save results to output directory.

        Args:
            fen_index: Dict mapping node_id to FEN string
            chapter_id: Chapter ID for output file naming
            tree_data: Optional tree JSON with UCI moves
            verbose: Print progress messages
            max_positions: Maximum positions to analyze

        Returns:
            Dict with node_id -> tags mapping (also saved to file)
        """
        # Run analysis
        results = self.run_fen_index(
            fen_index=fen_index,
            tree_data=tree_data,
            verbose=verbose,
            max_positions=max_positions,
        )

        # Convert to output format
        tags_output: Dict[str, Any] = {
            "metadata": {
                "chapter_id": chapter_id,
                "timestamp": datetime.now().isoformat(),
                "total_nodes": len(results),
                "depth": self.depth,
                "multipv": self.multipv,
            },
            "nodes": {}
        }

        for result in results:
            tags_output["nodes"][result.node_id] = {
                "tags": result.tags,
                "features": result.features,
                "error": result.error,
            }

        # Save to output directory
        output_path = self.output_dir / f"{chapter_id}.tags.json"
        with open(output_path, 'w') as f:
            json.dump(tags_output, f, indent=2)

        if verbose:
            logger.info(f"Tags saved to: {output_path}")

        if self.pgn_v2_repo:
            try:
                self.pgn_v2_repo.save_tags_json(
                    chapter_id=chapter_id,
                    tags_data=tags_output,
                    metadata={"chapter_id": chapter_id}
                )
                if verbose:
                    logger.info(f"Tags also saved to R2 for chapter {chapter_id}")
            except Exception as e:
                logger.error(f"Failed to save tags to R2 for chapter {chapter_id}: {e}")
        else:
            logger.warning("PgnV2Repo not configured, skipping R2 tags save.")

        return tags_output


__all__ = ["AnalysisPipeline"]
