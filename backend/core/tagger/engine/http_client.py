"""
HTTP-based Stockfish client for remote engine calls.
Implements the same interface as StockfishClient for compatibility.
"""
from typing import Dict, List, Tuple, Any, Optional
import requests
import chess
from ..models import Candidate


class HTTPStockfishClient:
    """Client for remote Stockfish engine via HTTP."""

    # Default timeout optimized for batch processing (100+ nodes in < 5s target)
    # Per-request timeout: 10s allows ~500ms average with headroom for retries
    DEFAULT_TIMEOUT = 10

    def __init__(self, base_url: str = "https://sf.cloudflare.com", timeout: int = None):
        """
        Initialize HTTP client.

        Args:
            base_url: Remote engine service URL
            timeout: Request timeout in seconds (default: 10s for batch optimization)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    def analyse_candidates(
        self,
        board: chess.Board,
        depth: int,
        multipv: int,
    ) -> Tuple[List[Candidate], int, Dict[str, Any]]:
        """
        Analyze position via remote HTTP endpoint.

        Args:
            board: Current position
            depth: Analysis depth
            multipv: Number of principal variations

        Returns:
            (candidates, best_score_cp, metadata)
        """
        fen = board.fen()

        resp = requests.get(
            f"{self.base_url}/analyze/stream",
            params={"fen": fen, "depth": depth, "multipv": multipv},
            timeout=self.timeout,
            stream=True,
        )
        resp.raise_for_status()

        # Parse SSE response
        multipv_data = {}
        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8") if isinstance(line, bytes) else line
            if decoded.startswith("data: "):
                content = decoded[6:]
                if content.startswith("info "):
                    parsed = self._parse_uci_info(content)
                    if parsed:
                        multipv_data[parsed["multipv"]] = parsed

        # Build candidates
        candidates = []
        best_score_cp = 0

        for idx, data in enumerate(sorted(multipv_data.values(), key=lambda x: x["multipv"])):
            move_uci = data["pv"][0] if data["pv"] else None
            if not move_uci:
                continue

            move = chess.Move.from_uci(move_uci)
            score_cp = data["score_cp"]

            if idx == 0:
                best_score_cp = score_cp

            kind = self._classify_move(board, move)
            candidates.append(Candidate(move=move, score_cp=score_cp, kind=kind))

        metadata = {
            "depth": depth,
            "multipv": multipv,
            "num_candidates": len(candidates),
            "source": "http",
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
        board_copy = board.copy()
        board_copy.push(move)
        fen = board_copy.fen()

        resp = requests.get(
            f"{self.base_url}/analyze/stream",
            params={"fen": fen, "depth": depth, "multipv": 1},
            timeout=self.timeout,
            stream=True,
        )
        resp.raise_for_status()

        # Parse best line score
        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8") if isinstance(line, bytes) else line
            if decoded.startswith("data: "):
                content = decoded[6:]
                if content.startswith("info "):
                    parsed = self._parse_uci_info(content)
                    if parsed and parsed["multipv"] == 1:
                        return parsed["score_cp"]

        return 0

    def _parse_uci_info(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse UCI info line to extract score and PV."""
        parts = content.split()
        if "multipv" not in parts or "score" not in parts or "pv" not in parts:
            return None

        try:
            multipv_idx = parts.index("multipv")
            score_idx = parts.index("score")
            pv_idx = parts.index("pv")

            multipv_num = int(parts[multipv_idx + 1])
            score_type = parts[score_idx + 1]
            score_value = int(parts[score_idx + 2])
            pv_moves = parts[pv_idx + 1:]

            # Convert to centipawns
            if score_type == "mate":
                score_cp = 10000 - abs(score_value) * 100 if score_value > 0 else -10000 + abs(score_value) * 100
            else:
                score_cp = score_value

            return {
                "multipv": multipv_num,
                "score_cp": score_cp,
                "pv": pv_moves,
            }
        except (ValueError, IndexError):
            return None

    def _classify_move(self, board: chess.Board, move: chess.Move) -> str:
        """Classify move as quiet, dynamic, or forcing."""
        if board.is_capture(move):
            return "forcing"

        board_copy = board.copy()
        board_copy.push(move)
        if board_copy.is_check():
            return "forcing"

        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            return "dynamic"

        return "quiet"


__all__ = ["HTTPStockfishClient"]
