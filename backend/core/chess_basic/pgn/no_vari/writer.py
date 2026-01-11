"""
chess_basic.pgn.no_vari.writer
不支持分支的 PGN 写入实现

Mainline-only PGN writer implementation.
"""

from typing import Optional
from ...types import Move, BoardState
from ..common.writer_base import PGNWriterBase
from ..common.pgn_types import PGNNode, PGNMove
from ..common.serialize import serialize_moves_mainline
from ..common.io import write_pgn_to_string


class PGNWriterNoVari(PGNWriterBase):
    """
    主线 PGN 写入器（不支持分支）
    Mainline PGN writer (no variation support)

    This writer records only the main line of play without any variations.
    It's simpler and more efficient than the variation-supporting writer.
    """

    def _reset_state(self) -> None:
        """重置内部状态 Reset internal state"""
        self._moves: list[PGNNode] = []
        self._move_number = 1
        self._is_white_turn = True

    def add_move(self, move: Move, state_before: BoardState, san: str) -> None:
        """
        添加走法到主线
        Add move to mainline

        Args:
            move: Move object
            state_before: Board state before the move
            san: SAN notation of the move

        Note: This method does NOT validate move legality or update board state.
        The caller is responsible for ensuring the move is legal.
        """
        pgn_move = PGNMove(san=san)
        node = PGNNode(move=pgn_move)
        self._moves.append(node)

        # 更新计数器 Update counters
        if not self._is_white_turn:
            self._move_number += 1
        self._is_white_turn = not self._is_white_turn

    def add_comment(self, comment: str) -> None:
        """
        添加评注到最后一个走法
        Add comment to last move

        Args:
            comment: Comment text
        """
        if self._moves:
            self._moves[-1].move.comment = comment

    def add_nag(self, nag: int) -> None:
        """
        添加 NAG 到最后一个走法
        Add NAG to last move

        Args:
            nag: Numeric Annotation Glyph
        """
        if self._moves:
            self._moves[-1].move.nags.append(nag)

    def to_pgn_string(self) -> str:
        """
        转换为 PGN 字符串
        Convert to PGN string

        Returns:
            Complete PGN string with tags and moves
        """
        # 序列化走法 Serialize moves
        movetext = serialize_moves_mainline(self._moves)

        # 获取结果 Get result
        result = self.tags.get("Result", "*")

        # 组装 PGN Assemble PGN
        return write_pgn_to_string(self.tags.get_all(), movetext, result)

    def get_move_count(self) -> int:
        """
        获取走法数量
        Get move count

        Returns:
            Number of moves recorded
        """
        return len(self._moves)

    def get_last_move(self) -> Optional[str]:
        """
        获取最后一个走法的 SAN
        Get SAN of last move

        Returns:
            SAN of last move, or None if no moves
        """
        if self._moves:
            return self._moves[-1].move.san
        return None

    def get_moves(self) -> list[str]:
        """
        获取所有走法的 SAN 列表
        Get list of all moves in SAN

        Returns:
            List of SAN strings
        """
        return [node.move.san for node in self._moves]
