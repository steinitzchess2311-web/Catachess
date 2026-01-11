"""
chess_basic.pgn.common.writer_base
PGN Writer 抽象基类

Abstract base class for PGN writers.
"""

from abc import ABC, abstractmethod
from typing import Optional
from ...types import Move, BoardState
from .tags import PGNTags


class PGNWriterBase(ABC):
    """
    PGN 写入器基类
    Base class for PGN writers

    This class defines the interface that all PGN writers must implement.
    Subclasses provide concrete implementations for different modes (no_vari, vari).
    """

    def __init__(self):
        self.tags = PGNTags()
        self._reset_state()

    @abstractmethod
    def _reset_state(self) -> None:
        """
        重置内部状态
        Reset internal state

        This method should initialize/reset all internal state variables.
        """
        pass

    @abstractmethod
    def add_move(self, move: Move, state_before: BoardState, san: str) -> None:
        """
        添加走法（核心方法）
        Add move (core method)

        Args:
            move: Move object
            state_before: Board state before the move
            san: SAN notation of the move

        Note: This method only records the move. It does NOT validate legality
        or modify the board state. The caller must ensure the move is legal.
        """
        pass

    @abstractmethod
    def to_pgn_string(self) -> str:
        """
        转换为 PGN 字符串
        Convert to PGN string

        Returns:
            Complete PGN string with tags and moves
        """
        pass

    def set_tag(self, key: str, value: str) -> None:
        """
        设置标签
        Set tag

        Args:
            key: Tag name
            value: Tag value
        """
        self.tags.set(key, value)

    def set_players(self, white: str, black: str) -> None:
        """设置对弈者 Set players"""
        self.tags.set_players(white, black)

    def set_event(self, event: str, site: str = "?", round_num: str = "?") -> None:
        """设置比赛信息 Set event information"""
        self.tags.set_event(event, site, round_num)

    def set_result(self, result: str) -> None:
        """设置结果 Set result"""
        self.tags.set_result(result)

    def add_comment(self, comment: str) -> None:
        """
        添加评注（可选实现）
        Add comment (optional implementation)

        Args:
            comment: Comment text
        """
        pass  # 子类可以选择实现 Subclasses may implement

    def reset(self) -> None:
        """
        重置写入器
        Reset writer

        Clears all tags and moves, ready for a new game.
        """
        self.tags = PGNTags()
        self._reset_state()

    def save_to_file(self, filepath: str) -> None:
        """
        保存到文件
        Save to file

        Args:
            filepath: Path to save PGN file
        """
        from .io import write_pgn_to_file
        pgn_string = self.to_pgn_string()
        write_pgn_to_file(pgn_string, filepath)
