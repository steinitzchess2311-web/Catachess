"""Adapter: convert R2 tree JSON → variation-like objects for Opening Trainer.

The patch editor saves chapter trees to R2 as SAN-only JSON (no FEN, no UCI).
The Opening Trainer service expects variation objects with FEN, UCI, move_number,
color, rank — the same shape as SQL Variation rows.

This module bridges the gap: given a StudyTreeDTO (from R2), it replays moves
using python-chess to compute the missing fields and returns a list of
SyntheticVariation objects that are structurally compatible with what
variation_repo.get_variations_for_chapter() returns.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import chess

logger = logging.getLogger(__name__)

STANDARD_START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@dataclass
class SyntheticVariation:
    """Drop-in replacement for a SQL Variation row, built from R2 tree JSON.

    Field names intentionally mirror the SQLAlchemy Variation table so that
    service.py can access them via getattr() without any changes.
    """

    id: str
    parent_id: str | None
    san: str
    uci: str
    fen: str          # FEN of the position AFTER this move
    move_number: int
    color: str        # 'white' or 'black'
    rank: int         # 0 = main line, 1+ = alternative


def build_variations_from_r2_tree(
    tree: Any,  # StudyTreeDTO — typed as Any to avoid hard import cycle
    starting_fen: str | None = None,
) -> list[SyntheticVariation]:
    """Walk a StudyTreeDTO and return a flat list of SyntheticVariation objects.

    The list is structurally equivalent to the output of
    variation_repo.get_variations_for_chapter(), so it can be passed directly
    to service.build_unit_catalog() without any changes to the service layer.

    Args:
        tree: StudyTreeDTO loaded from R2.
        starting_fen: Custom starting position for the chapter (None = standard).

    Returns:
        Flat list of SyntheticVariation objects in DFS order.
    """
    root_node = tree.nodes.get(tree.rootId)
    if not root_node:
        return []

    start_fen = starting_fen or STANDARD_START_FEN
    try:
        board = chess.Board(start_fen)
    except Exception:
        logger.warning(
            "r2_adapter: invalid starting FEN %r — falling back to standard start", starting_fen
        )
        board = chess.Board()

    result: list[SyntheticVariation] = []

    def dfs(
        node_id: str,
        parent_id: str | None,
        board: chess.Board,
        move_number: int,
        color: str,
        rank: int,
    ) -> None:
        node = tree.nodes.get(node_id)
        if not node or not node.san:
            return

        try:
            move = board.parse_san(node.san)
        except Exception:
            logger.warning(
                "r2_adapter: cannot parse SAN %r at node %s — skipping subtree",
                node.san,
                node_id,
            )
            return

        uci = move.uci()
        board.push(move)
        fen_after = board.fen()

        result.append(
            SyntheticVariation(
                id=node_id,
                parent_id=parent_id,
                san=node.san,
                uci=uci,
                fen=fen_after,
                move_number=move_number,
                color=color,
                rank=rank,
            )
        )

        next_color = "black" if color == "white" else "white"
        next_move_number = move_number + (1 if color == "black" else 0)

        for i, child_id in enumerate(node.children):
            dfs(child_id, node_id, board, next_move_number, next_color, i)

        board.pop()

    initial_color = "white" if board.turn == chess.WHITE else "black"
    initial_move_number = board.fullmove_number

    # Root node's children become top-level moves (parent_id=None), matching
    # what SQL variation rows have for the first move of a chapter.
    for i, child_id in enumerate(root_node.children):
        dfs(child_id, None, board, initial_move_number, initial_color, i)

    return result
