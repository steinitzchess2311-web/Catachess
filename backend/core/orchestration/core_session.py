"""
orchestration.core_session
单局对弈/研究会话控制器

Single game/study session controller.
"""

from typing import Optional
from ..chess_basic.types import BoardState, Move
from ..chess_basic.constants import GameResult, TerminationReason
from ..chess_basic.rule.api import (
    is_legal_move,
    apply_move,
    generate_legal_moves,
    is_checkmate,
    is_stalemate,
    get_game_result,
)
from ..chess_basic.utils.fen import parse_fen, board_to_fen, get_starting_position
from ..chess_basic.utils.san import move_to_san, needs_disambiguation
from ..chess_basic.rule.check import gives_check, is_in_checkmate
from ..chess_basic.pgn.no_vari.writer import PGNWriterNoVari
from ..chess_basic.pgn.vari.writer import PGNWriterVari
from ..chess_basic.pgn.common.writer_base import PGNWriterBase
from ..chess_basic.errors import IllegalMoveError
from .policies import GamePolicy, StandardGamePolicy


class CoreSession:
    """
    核心会话控制器
    Core session controller

    Manages a single chess game or analysis session. Enforces the call order:
    1. Validate move with rule engine
    2. Apply move with rule engine
    3. Record move with PGN writer (if policy allows)

    RED LINE: This class guarantees that illegal moves NEVER reach PGN writer.
    """

    def __init__(
        self,
        policy: Optional[GamePolicy] = None,
        starting_fen: Optional[str] = None
    ):
        """
        初始化会话
        Initialize session

        Args:
            policy: Game policy (defaults to StandardGamePolicy)
            starting_fen: Starting position FEN (defaults to standard starting position)
        """
        self.policy = policy or StandardGamePolicy()

        # 初始化棋盘状态 Initialize board state
        if starting_fen:
            self.state = parse_fen(starting_fen)
        else:
            self.state = get_starting_position()

        self._starting_fen = board_to_fen(self.state)

        # 初始化 PGN 写入器 Initialize PGN writer
        if self.policy.records_pgn():
            if self.policy.allows_variations():
                self._pgn_writer: Optional[PGNWriterBase] = PGNWriterVari()
            else:
                self._pgn_writer: Optional[PGNWriterBase] = PGNWriterNoVari()
        else:
            self._pgn_writer = None

        # 对局状态 Game status
        self._is_game_over = False
        self._game_result: Optional[GameResult] = None
        self._termination_reason: Optional[TerminationReason] = None

        # 走法历史（用于悔棋）Move history (for takebacks)
        self._move_history: list[tuple[Move, BoardState]] = []

    def submit_move(self, move: Move) -> bool:
        """
        提交走法（核心方法）
        Submit move (core method)

        This method enforces the critical order:
        1. Rule validation
        2. Rule application
        3. PGN recording

        Args:
            move: Move to submit

        Returns:
            True if move was legal and applied, False otherwise

        Raises:
            IllegalMoveError: If move is illegal
        """
        if self._is_game_over and self.policy.auto_ends_on_checkmate():
            raise IllegalMoveError("Game is over")

        # 步骤 1：规则验证 Step 1: Rule validation
        if not is_legal_move(self.state, move):
            raise IllegalMoveError(f"Move {move.to_uci()} is not legal in current position")

        # 保存当前状态（用于悔棋和 PGN）Save current state (for takeback and PGN)
        state_before = self.state.copy()

        # 步骤 2：规则应用 Step 2: Rule application
        self.state = apply_move(self.state, move)

        # 步骤 3：PGN 记录 Step 3: PGN recording
        if self._pgn_writer:
            san = self._compute_san(move, state_before)
            self._pgn_writer.add_move(move, state_before, san)

        # 保存到历史 Save to history
        self._move_history.append((move, state_before))

        # 检查对局是否结束 Check if game is over
        self._check_game_over()

        return True

    def _compute_san(self, move: Move, state_before: BoardState) -> str:
        """
        计算走法的 SAN 表示
        Compute SAN notation for move

        Args:
            move: Move object
            state_before: Board state before the move

        Returns:
            SAN string
        """
        # 检查是否将军或将死 Check if gives check or checkmate
        is_check = gives_check(state_before, move)
        is_checkmate_result = is_in_checkmate(self.state)

        # 检查是否为捕获 Check if capture
        is_capture = state_before.get_piece(move.to_square) is not None

        # 计算消歧义 Compute disambiguation
        legal_moves = generate_legal_moves(state_before)
        piece = state_before.get_piece(move.from_square)
        disambiguation = None
        if piece:
            disambiguation = needs_disambiguation(
                piece, move.from_square, move.to_square, state_before, legal_moves
            )

        return move_to_san(
            move,
            state_before,
            is_check=is_check,
            is_checkmate=is_checkmate_result,
            is_capture=is_capture,
            disambiguation=disambiguation,
        )

    def _check_game_over(self) -> None:
        """检查对局是否结束 Check if game is over"""
        result, reason = get_game_result(self.state)

        if result != GameResult.IN_PROGRESS:
            self._is_game_over = True
            self._game_result = result
            self._termination_reason = reason

            if self._pgn_writer:
                self._pgn_writer.set_result(result.value)

    def is_game_over(self) -> bool:
        """对局是否结束 Is game over"""
        return self._is_game_over

    def get_result(self) -> tuple[Optional[GameResult], Optional[TerminationReason]]:
        """获取对局结果 Get game result"""
        return (self._game_result, self._termination_reason)

    def get_current_state(self) -> BoardState:
        """获取当前棋盘状态 Get current board state"""
        return self.state.copy()

    def get_legal_moves(self) -> list[Move]:
        """获取当前所有合法走法 Get all legal moves"""
        return generate_legal_moves(self.state)

    def get_pgn(self) -> Optional[str]:
        """
        获取 PGN 字符串
        Get PGN string

        Returns:
            PGN string if recording is enabled, None otherwise
        """
        if self._pgn_writer:
            return self._pgn_writer.to_pgn_string()
        return None

    def get_fen(self) -> str:
        """获取当前 FEN Get current FEN"""
        return board_to_fen(self.state)

    def takeback(self) -> bool:
        """
        悔棋
        Takeback last move

        Returns:
            True if takeback successful, False if no moves to take back
        """
        if not self.policy.allows_takebacks():
            return False

        if not self._move_history:
            return False

        # 恢复到上一个状态 Restore to previous state
        _, previous_state = self._move_history.pop()
        self.state = previous_state

        # 重置对局结束标志 Reset game over flag
        self._is_game_over = False
        self._game_result = None
        self._termination_reason = None

        return True

    def set_pgn_tag(self, key: str, value: str) -> None:
        """
        设置 PGN 标签
        Set PGN tag

        Args:
            key: Tag name
            value: Tag value
        """
        if self._pgn_writer:
            self._pgn_writer.set_tag(key, value)

    def reset(self, starting_fen: Optional[str] = None) -> None:
        """
        重置会话
        Reset session

        Args:
            starting_fen: New starting position (uses original if None)
        """
        if starting_fen:
            self.state = parse_fen(starting_fen)
            self._starting_fen = starting_fen
        else:
            self.state = parse_fen(self._starting_fen)

        self._is_game_over = False
        self._game_result = None
        self._termination_reason = None
        self._move_history.clear()

        if self._pgn_writer:
            self._pgn_writer.reset()
