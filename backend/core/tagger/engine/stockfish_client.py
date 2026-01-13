"""
Stockfish engine client implementation.
Keep under 150 lines as per refactoring plan.
"""
from typing import Dict, List, Tuple, Any, Optional
import chess
import chess.engine
from ..models import Candidate
from ..config.engine import DEFAULT_STOCKFISH_PATH


class StockfishClient:
    """Wrapper around python-chess Stockfish engine."""

    def __init__(self, engine_path: Optional[str] = None):
        """
        Initialize Stockfish client.

        Args:
            engine_path: Path to Stockfish binary. If None, uses default.
        """
        self.engine_path = engine_path or DEFAULT_STOCKFISH_PATH
        self._engine: Optional[chess.engine.SimpleEngine] = None

    def __enter__(self):
        """Context manager entry."""
        self._engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._engine:
            self._engine.quit()
            self._engine = None

    def analyse_candidates(
        self,
        board: chess.Board,
        depth: int,
        multipv: int,
    ) -> Tuple[List[Candidate], int, Dict[str, Any]]:
        """
        Analyze position and return top N candidate moves.

        Args:
            board: Current position
            depth: Analysis depth
            multipv: Number of principal variations

        Returns:
            (candidates, best_score_cp, metadata)
        """
        if not self._engine:
            raise RuntimeError("Engine not initialized. Use as context manager.")

        # Analyze with MultiPV
        result = self._engine.analyse(
            board,
            chess.engine.Limit(depth=depth),
            multipv=multipv
        )

        candidates = []
        best_score_cp = 0

        for idx, info in enumerate(result):
            if "pv" not in info or not info["pv"]:
                continue

            move = info["pv"][0]
            score = info.get("score", chess.engine.Cp(0))

            # Convert score to centipawns from current player's perspective
            score_cp = self._score_to_cp(score, board.turn)

            if idx == 0:
                best_score_cp = score_cp

            # Classify move kind
            kind = self._classify_move(board, move)

            candidates.append(Candidate(
                move=move,
                score_cp=score_cp,
                kind=kind
            ))

        metadata = {
            "depth": depth,
            "multipv": multipv,
            "num_candidates": len(candidates),
        }

        return candidates, best_score_cp, metadata

    def eval_specific(
        self,
        board: chess.Board,
        move: chess.Move,
        depth: int,
    ) -> int:
        """
        Evaluate position after a specific move.

        Args:
            board: Board before move
            move: Move to evaluate
            depth: Analysis depth

        Returns:
            Evaluation in centipawns
        """
        if not self._engine:
            raise RuntimeError("Engine not initialized. Use as context manager.")

        # Make the move on a copy
        board_copy = board.copy()
        board_copy.push(move)

        # Analyze the resulting position
        info = self._engine.analyse(
            board_copy,
            chess.engine.Limit(depth=depth)
        )

        score = info.get("score", chess.engine.Cp(0))
        # Note: After the move, it's the opponent's turn
        return self._score_to_cp(score, board_copy.turn)

    def _score_to_cp(self, score: chess.engine.Score, turn: chess.Color) -> int:
        """
        Convert engine score to centipawns from current player perspective.

        Args:
            score: Engine score object
            turn: Current player to move

        Returns:
            Score in centipawns
        """
        # Get relative score (from white's perspective)
        if score.is_mate():
            # Mate scores: use large values
            mate_in = score.relative.mate()
            if mate_in > 0:
                cp = 10000 - mate_in * 100
            else:
                cp = -10000 - mate_in * 100
        else:
            cp = score.relative.score(mate_score=10000)

        # Flip if black to move
        if turn == chess.BLACK:
            cp = -cp

        return cp

    def _classify_move(self, board: chess.Board, move: chess.Move) -> str:
        """
        Classify move as quiet, dynamic, or forcing.

        Args:
            board: Position before move
            move: Move to classify

        Returns:
            "quiet", "dynamic", or "forcing"
        """
        # Forcing: captures and checks
        if board.is_capture(move):
            return "forcing"

        board_copy = board.copy()
        board_copy.push(move)
        if board_copy.is_check():
            return "forcing"

        # Dynamic: pawn pushes, piece developments to active squares
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            return "dynamic"

        # Otherwise quiet
        return "quiet"


__all__ = ["StockfishClient"]
