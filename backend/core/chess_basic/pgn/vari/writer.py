"""
chess_basic.pgn.vari.writer
支持变化分支的 PGN 写入实现

Variation-supporting PGN writer implementation.
"""

from typing import Optional
from ...types import Move, BoardState
from ..common.writer_base import PGNWriterBase
from ..common.pgn_types import PGNNode, PGNMove
from ..common.serialize import serialize_comment, format_nag
from ..common.io import write_pgn_to_string
from .variation_stack import VariationStack


class PGNWriterVari(PGNWriterBase):
    """
    支持分支的 PGN 写入器
    Variation-supporting PGN writer

    This writer supports full PGN game trees with variations and sub-variations.
    """

    def _reset_state(self) -> None:
        """重置内部状态 Reset internal state"""
        self._stack = VariationStack()
        self._move_number = 1
        self._is_white_turn = True

    def add_move(self, move: Move, state_before: BoardState, san: str) -> None:
        """
        添加走法
        Add move

        Args:
            move: Move object
            state_before: Board state before the move
            san: SAN notation of the move

        Note: This method does NOT validate move legality or update board state.
        """
        pgn_move = PGNMove(san=san)
        node = PGNNode(move=pgn_move)
        self._stack.add_move(node)

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
        current_level = self._stack.get_current_level()
        if current_level:
            current_level[-1].move.comment = comment

    def add_nag(self, nag: int) -> None:
        """
        添加 NAG 到最后一个走法
        Add NAG to last move

        Args:
            nag: Numeric Annotation Glyph
        """
        current_level = self._stack.get_current_level()
        if current_level:
            current_level[-1].move.nags.append(nag)

    def start_variation(self) -> None:
        """
        开始新分支
        Start new variation

        Call this before adding moves to a variation.
        """
        self._stack.start_variation()

    def end_variation(self) -> None:
        """
        结束当前分支
        End current variation

        Call this after adding all moves in a variation.
        """
        self._stack.end_variation()

    def to_pgn_string(self) -> str:
        """
        转换为 PGN 字符串
        Convert to PGN string

        Returns:
            Complete PGN string with tags, moves, and variations
        """
        # 序列化走法树 Serialize move tree
        movetext = self._serialize_move_tree()

        # 获取结果 Get result
        result = self.tags.get("Result", "*")

        # 组装 PGN Assemble PGN
        return write_pgn_to_string(self.tags.get_all(), movetext, result)

    def _serialize_move_tree(self) -> str:
        """
        序列化走法树（包含分支）
        Serialize move tree (including variations)

        Returns:
            PGN movetext with variations
        """
        mainline = self._stack.get_mainline()
        if not mainline:
            return "*"

        parts = []
        self._serialize_nodes(mainline, parts, move_number=1, is_white=True)

        return " ".join(parts)

    def _serialize_nodes(
        self,
        nodes: list[PGNNode],
        parts: list[str],
        move_number: int,
        is_white: bool
    ) -> tuple[int, bool]:
        """
        递归序列化节点（包含分支）
        Recursively serialize nodes (including variations)

        Args:
            nodes: List of nodes to serialize
            parts: Output list to append to
            move_number: Current move number
            is_white: Whether current move is white's

        Returns:
            Tuple of (next_move_number, next_is_white)
        """
        for i, node in enumerate(nodes):
            move = node.move

            # 添加回合号 Add move number
            if is_white:
                parts.append(f"{move_number}.")
                parts.append(move.san)
            else:
                # 黑方走法 Black's move
                if i == 0 and len(parts) == 0:
                    # 如果是第一个走法且是黑方，需要显示回合号
                    # If first move and black's turn, show move number
                    parts.append(f"{move_number}...")
                parts.append(move.san)

            # 添加 NAG Add NAGs
            for nag in move.nags:
                parts.append(format_nag(nag))

            # 添加评注 Add comment
            if move.comment:
                from ..common.serialize import serialize_comment
                parts.append(serialize_comment(move.comment))

            # 处理分支 Handle variations
            if node.variations:
                for variation_root in node.variations:
                    # 开始分支括号 Start variation parenthesis
                    parts.append("(")

                    # 序列化分支 Serialize variation
                    # 分支从父走法之后开始，所以回合号和颜色需要恢复
                    # Variation starts after parent move, so restore move number and color
                    var_move_num = move_number
                    var_is_white = is_white

                    # 如果父走法是黑方，分支从下一个回合开始
                    # If parent move is black's, variation starts from next move
                    if not is_white:
                        var_move_num += 1
                        var_is_white = True

                    # 构建分支节点列表 Build variation node list
                    variation_nodes = [variation_root]
                    current = variation_root
                    while current.variations:
                        # 简化：只取第一个分支 Simplified: only take first variation
                        current = current.variations[0]
                        variation_nodes.append(current)

                    self._serialize_nodes(
                        variation_nodes,
                        parts,
                        var_move_num,
                        var_is_white
                    )

                    # 结束分支括号 End variation parenthesis
                    parts.append(")")

            # 更新计数器 Update counters
            if not is_white:
                move_number += 1
            is_white = not is_white

        return (move_number, is_white)

    def get_move_count(self) -> int:
        """
        获取主线走法数量
        Get mainline move count

        Returns:
            Number of moves in mainline
        """
        return len(self._stack.get_mainline())

    def is_in_variation(self) -> bool:
        """
        检查是否在分支中
        Check if currently in a variation

        Returns:
            True if in variation, False if in mainline
        """
        return self._stack.is_in_variation()
