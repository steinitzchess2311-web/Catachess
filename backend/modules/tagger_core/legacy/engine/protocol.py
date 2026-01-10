"""
Engine protocol definition.
"""
from typing import Dict, List, Protocol, Tuple, Any
import chess
from ...models import Candidate


class EngineClient(Protocol):
    """Protocol for chess engine clients."""

    def analyse_candidates(
        self,
        board: chess.Board,
        depth: int,
        multipv: int,
    ) -> Tuple[List[Candidate], int, Dict[str, Any]]:
        """
        Analyze the position and return candidate moves.

        Args:
            board: Current chess position
            depth: Analysis depth
            multipv: Number of principal variations to analyze

        Returns:
            Tuple of (candidates, best_score_cp, engine_metadata)
        """
        ...

    def eval_specific(
        self,
        board: chess.Board,
        move: chess.Move,
        depth: int,
    ) -> int:
        """
        Evaluate a specific move.

        Args:
            board: Board before the move
            move: Move to evaluate
            depth: Analysis depth

        Returns:
            Evaluation in centipawns
        """
        ...


__all__ = ["EngineClient"]
