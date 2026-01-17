"""
PGN to FEN helper.

Converts PGN mainline to a FEN position at a requested ply or move.
Uses python-chess for PGN parsing to avoid duplicating chess logic.
"""
from __future__ import annotations

import io
from typing import Optional

import chess
import chess.pgn


def fen_from_pgn(
    pgn: str,
    *,
    ply: Optional[int] = None,
    move_number: Optional[int] = None,
    color: Optional[str] = None,
    san: Optional[str] = None,
) -> str:
    """
    Return FEN from a PGN mainline.

    Args:
        pgn: Full PGN string (tags + movetext).
        ply: 1-based ply index into the mainline (0 returns starting position).
        move_number: Fullmove number (1, 2, 3, ...).
        color: "w" or "b" for move_number lookup.
        san: Optional SAN filter when using move_number/color.
    """
    if not pgn or not pgn.strip():
        raise ValueError("PGN is empty")

    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        raise ValueError("PGN could not be parsed")

    board = game.board()

    if ply is not None:
        if ply < 0:
            raise ValueError("ply must be >= 0")
        if ply == 0:
            return board.fen()
        for index, move in enumerate(game.mainline_moves(), start=1):
            board.push(move)
            if index == ply:
                return board.fen()
        raise ValueError("ply exceeds PGN length")

    if move_number is None:
        for move in game.mainline_moves():
            board.push(move)
        return board.fen()

    if color not in ("w", "b"):
        raise ValueError("color must be 'w' or 'b' when move_number is provided")

    for move in game.mainline_moves():
        current_move_number = board.fullmove_number
        current_color = "w" if board.turn == chess.WHITE else "b"
        current_san = board.san(move)
        board.push(move)
        if current_move_number == move_number and current_color == color:
            if san and current_san != san:
                continue
            return board.fen()

    raise ValueError("Move not found in PGN")
