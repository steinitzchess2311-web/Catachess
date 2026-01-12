"""
PGN file processor for extracting positions and moves.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List

import chess
import chess.pgn


@dataclass
class Position:
    """Represents a position from a PGN game."""
    game_index: int
    move_number: int
    fen: str
    played_move_uci: str
    game_headers: dict


class PGNProcessor:
    """Processes PGN files and extracts positions for analysis."""

    def __init__(self, pgn_path: Path):
        """
        Initialize PGN processor.

        Args:
            pgn_path: Path to PGN file to process
        """
        self.pgn_path = pgn_path

    def extract_positions(self, skip_opening_moves: int = 0) -> Iterator[Position]:
        """
        Extract all positions from the PGN file.

        Args:
            skip_opening_moves: Number of opening moves to skip (default: 0)

        Yields:
            Position objects containing FEN, played move, and metadata
        """
        with open(self.pgn_path) as pgn_file:
            game_index = 0

            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break

                headers = dict(game.headers)
                board = game.board()
                node = game
                move_number = 0

                # Traverse the game
                while node.variations:
                    node = node.variation(0)
                    move_number += 1

                    # Skip opening moves if requested
                    if move_number <= skip_opening_moves:
                        board.push(node.move)
                        continue

                    # Get FEN before the move
                    fen_before = board.fen()
                    played_move = node.move

                    yield Position(
                        game_index=game_index,
                        move_number=move_number,
                        fen=fen_before,
                        played_move_uci=played_move.uci(),
                        game_headers=headers
                    )

                    # Apply the move for next iteration
                    board.push(played_move)

                game_index += 1

    def count_games(self) -> int:
        """
        Count total number of games in PGN file.

        Returns:
            Number of games
        """
        with open(self.pgn_path) as pgn_file:
            count = 0
            while chess.pgn.read_game(pgn_file) is not None:
                count += 1
        return count


__all__ = ["PGNProcessor", "Position"]
