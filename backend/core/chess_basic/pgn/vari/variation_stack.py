"""
chess_basic.pgn.vari.variation_stack
PGN 分支栈与括号管理

PGN variation stack and parenthesis management.
"""

from dataclasses import dataclass
from typing import Optional
from ..common.pgn_types import PGNNode


@dataclass
class VariationLevel:
    """
    分支层级
    Variation level

    Attributes:
        nodes: Nodes at this level
        parent_node: Parent node (where variation branches from)
    """
    nodes: list[PGNNode]
    parent_node: Optional[PGNNode] = None


class VariationStack:
    """
    分支栈
    Variation stack

    Manages the hierarchy of variations in a PGN game tree.
    """

    def __init__(self):
        self._stack: list[VariationLevel] = []
        self._mainline: list[PGNNode] = []
        self._current_level: list[PGNNode] = self._mainline

    def get_mainline(self) -> list[PGNNode]:
        """
        获取主线
        Get mainline

        Returns:
            List of mainline nodes
        """
        return self._mainline

    def get_current_level(self) -> list[PGNNode]:
        """
        获取当前层级
        Get current level

        Returns:
            List of nodes at current level
        """
        return self._current_level

    def add_move(self, node: PGNNode) -> None:
        """
        添加走法到当前层级
        Add move to current level

        Args:
            node: Node to add
        """
        self._current_level.append(node)

    def start_variation(self) -> None:
        """
        开始新分支
        Start new variation

        Creates a new variation level. The variation will branch from the
        last move of the current level.
        """
        if not self._current_level:
            raise ValueError("Cannot start variation: no moves at current level")

        # 获取分支起点（当前层级的最后一个走法）
        # Get variation starting point (last move of current level)
        parent_node = self._current_level[-1]

        # 创建新层级 Create new level
        new_level = VariationLevel(nodes=[], parent_node=parent_node)
        self._stack.append(new_level)

        # 切换到新层级 Switch to new level
        self._current_level = new_level.nodes

    def end_variation(self) -> None:
        """
        结束当前分支
        End current variation

        Returns to the parent level and adds the variation to the parent node.
        """
        if not self._stack:
            raise ValueError("Cannot end variation: not in a variation")

        # 获取当前层级 Get current level
        current_level = self._stack.pop()

        # 将当前层级添加到父节点的分支列表
        # Add current level to parent node's variation list
        if current_level.parent_node and current_level.nodes:
            current_level.parent_node.variations.append(current_level.nodes[0])

        # 返回到父层级 Return to parent level
        if self._stack:
            self._current_level = self._stack[-1].nodes
        else:
            self._current_level = self._mainline

    def is_in_variation(self) -> bool:
        """
        检查是否在分支中
        Check if currently in a variation

        Returns:
            True if in variation, False if in mainline
        """
        return len(self._stack) > 0

    def get_depth(self) -> int:
        """
        获取当前分支深度
        Get current variation depth

        Returns:
            Depth (0 for mainline, 1+ for variations)
        """
        return len(self._stack)

    def reset(self) -> None:
        """
        重置栈
        Reset stack

        Clears all variations and returns to empty mainline.
        """
        self._stack.clear()
        self._mainline.clear()
        self._current_level = self._mainline
