"""
orchestration.policies
比赛/研究等模式策略定义

Game mode policies (standard game, analysis, etc.).
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional


class SessionMode(Enum):
    """
    会话模式
    Session mode

    Defines different types of chess sessions.
    """
    STANDARD_GAME = "standard_game"  # 标准对局 Standard game
    ANALYSIS = "analysis"            # 分析模式 Analysis mode
    PUZZLE = "puzzle"                # 谜题 Puzzle
    STUDY = "study"                  # 研究 Study


class GamePolicy(ABC):
    """
    对局策略基类
    Base class for game policies

    Defines rules and constraints for different game modes.
    """

    @abstractmethod
    def allows_variations(self) -> bool:
        """
        是否允许分支
        Whether variations are allowed

        Returns:
            True if variations allowed, False otherwise
        """
        pass

    @abstractmethod
    def allows_takebacks(self) -> bool:
        """
        是否允许悔棋
        Whether takebacks are allowed

        Returns:
            True if takebacks allowed, False otherwise
        """
        pass

    @abstractmethod
    def enforces_time_control(self) -> bool:
        """
        是否强制时间控制
        Whether time control is enforced

        Returns:
            True if time control enforced, False otherwise
        """
        pass

    @abstractmethod
    def auto_ends_on_checkmate(self) -> bool:
        """
        是否将死后自动结束
        Whether game auto-ends on checkmate

        Returns:
            True if auto-ends, False otherwise
        """
        pass

    @abstractmethod
    def records_pgn(self) -> bool:
        """
        是否记录 PGN
        Whether to record PGN

        Returns:
            True if PGN should be recorded, False otherwise
        """
        pass

    def get_description(self) -> str:
        """
        获取策略描述
        Get policy description

        Returns:
            Description string
        """
        return self.__class__.__name__


class StandardGamePolicy(GamePolicy):
    """
    标准对局策略
    Standard game policy

    - No variations
    - No takebacks
    - Time control enforced (if set)
    - Auto-ends on checkmate
    - Records PGN
    """

    def allows_variations(self) -> bool:
        return False

    def allows_takebacks(self) -> bool:
        return False

    def enforces_time_control(self) -> bool:
        return True

    def auto_ends_on_checkmate(self) -> bool:
        return True

    def records_pgn(self) -> bool:
        return True

    def get_description(self) -> str:
        return "Standard game with no takebacks"


class AnalysisPolicy(GamePolicy):
    """
    分析策略
    Analysis policy

    - Allows variations
    - Allows takebacks
    - No time control
    - Does not auto-end
    - Records PGN with variations
    """

    def allows_variations(self) -> bool:
        return True

    def allows_takebacks(self) -> bool:
        return True

    def enforces_time_control(self) -> bool:
        return False

    def auto_ends_on_checkmate(self) -> bool:
        return False

    def records_pgn(self) -> bool:
        return True

    def get_description(self) -> str:
        return "Analysis mode with variations and takebacks"


class PuzzlePolicy(GamePolicy):
    """
    谜题策略
    Puzzle policy

    - No variations
    - Allows takebacks
    - No time control
    - Does not auto-end (waits for solution)
    - Does not record PGN
    """

    def allows_variations(self) -> bool:
        return False

    def allows_takebacks(self) -> bool:
        return True

    def enforces_time_control(self) -> bool:
        return False

    def auto_ends_on_checkmate(self) -> bool:
        return False

    def records_pgn(self) -> bool:
        return False

    def get_description(self) -> str:
        return "Puzzle mode with takebacks but no PGN recording"


class StudyPolicy(GamePolicy):
    """
    研究策略
    Study policy

    - Allows variations
    - Allows takebacks
    - No time control
    - Does not auto-end
    - Records PGN with variations
    """

    def allows_variations(self) -> bool:
        return True

    def allows_takebacks(self) -> bool:
        return True

    def enforces_time_control(self) -> bool:
        return False

    def auto_ends_on_checkmate(self) -> bool:
        return False

    def records_pgn(self) -> bool:
        return True

    def get_description(self) -> str:
        return "Study mode with full variation support"


def get_policy_for_mode(mode: SessionMode) -> GamePolicy:
    """
    根据会话模式获取对应策略
    Get policy for session mode

    Args:
        mode: Session mode

    Returns:
        Appropriate GamePolicy instance
    """
    policies = {
        SessionMode.STANDARD_GAME: StandardGamePolicy(),
        SessionMode.ANALYSIS: AnalysisPolicy(),
        SessionMode.PUZZLE: PuzzlePolicy(),
        SessionMode.STUDY: StudyPolicy(),
    }
    return policies.get(mode, StandardGamePolicy())
