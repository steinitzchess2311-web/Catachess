"""
orchestration.core_facade
core 对外唯一调用门面

Core facade - single external interface to core module.
"""

from typing import Optional
from ..chess_basic.types import Move, BoardState
from ..chess_basic.constants import GameResult, TerminationReason
from ..chess_basic.utils.uci import parse_uci_move
from ..chess_basic.utils.fen import parse_fen
from ..chess_basic.errors import ChessError
from .core_session import CoreSession
from .policies import SessionMode, GamePolicy, get_policy_for_mode


class CoreFacade:
    """
    Core 模块对外唯一门面
    Core module facade

    This is the ONLY interface that external modules (frontend, network, user system)
    should use to interact with the core chess engine.

    RED LINES:
    - Frontend/network code MUST NOT import from chess_basic or rule modules directly
    - All interactions MUST go through this facade
    - This facade ensures proper orchestration of rule validation and PGN recording
    """

    def __init__(self):
        self._active_sessions: dict[str, CoreSession] = {}

    def create_session(
        self,
        session_id: str,
        mode: SessionMode = SessionMode.STANDARD_GAME,
        starting_fen: Optional[str] = None,
        custom_policy: Optional[GamePolicy] = None
    ) -> str:
        """
        创建新会话
        Create new session

        Args:
            session_id: Unique session identifier
            mode: Session mode
            starting_fen: Starting position FEN
            custom_policy: Custom game policy (overrides mode)

        Returns:
            Session ID

        Raises:
            ValueError: If session_id already exists
        """
        if session_id in self._active_sessions:
            raise ValueError(f"Session {session_id} already exists")

        policy = custom_policy or get_policy_for_mode(mode)
        session = CoreSession(policy=policy, starting_fen=starting_fen)
        self._active_sessions[session_id] = session

        return session_id

    def get_session(self, session_id: str) -> CoreSession:
        """
        获取会话
        Get session

        Args:
            session_id: Session identifier

        Returns:
            CoreSession instance

        Raises:
            ValueError: If session not found
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")
        return self._active_sessions[session_id]

    def close_session(self, session_id: str) -> None:
        """
        关闭会话
        Close session

        Args:
            session_id: Session identifier
        """
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

    def submit_move_uci(self, session_id: str, uci: str) -> bool:
        """
        提交 UCI 格式走法
        Submit move in UCI format

        Args:
            session_id: Session identifier
            uci: UCI move string (e.g., 'e2e4')

        Returns:
            True if move was legal and applied

        Raises:
            ChessError: If move is illegal or session not found
        """
        session = self.get_session(session_id)
        move = parse_uci_move(uci)
        return session.submit_move(move)

    def submit_move(self, session_id: str, move: Move) -> bool:
        """
        提交走法
        Submit move

        Args:
            session_id: Session identifier
            move: Move object

        Returns:
            True if move was legal and applied

        Raises:
            ChessError: If move is illegal or session not found
        """
        session = self.get_session(session_id)
        return session.submit_move(move)

    def get_legal_moves(self, session_id: str) -> list[str]:
        """
        获取所有合法走法（UCI 格式）
        Get all legal moves (UCI format)

        Args:
            session_id: Session identifier

        Returns:
            List of UCI move strings
        """
        session = self.get_session(session_id)
        moves = session.get_legal_moves()
        return [move.to_uci() for move in moves]

    def get_board_state(self, session_id: str) -> BoardState:
        """
        获取棋盘状态
        Get board state

        Args:
            session_id: Session identifier

        Returns:
            Current board state
        """
        session = self.get_session(session_id)
        return session.get_current_state()

    def get_fen(self, session_id: str) -> str:
        """
        获取当前 FEN
        Get current FEN

        Args:
            session_id: Session identifier

        Returns:
            FEN string
        """
        session = self.get_session(session_id)
        return session.get_fen()

    def get_pgn(self, session_id: str) -> Optional[str]:
        """
        获取 PGN
        Get PGN

        Args:
            session_id: Session identifier

        Returns:
            PGN string if recording is enabled, None otherwise
        """
        session = self.get_session(session_id)
        return session.get_pgn()

    def is_game_over(self, session_id: str) -> bool:
        """
        检查对局是否结束
        Check if game is over

        Args:
            session_id: Session identifier

        Returns:
            True if game is over
        """
        session = self.get_session(session_id)
        return session.is_game_over()

    def get_result(self, session_id: str) -> tuple[Optional[GameResult], Optional[TerminationReason]]:
        """
        获取对局结果
        Get game result

        Args:
            session_id: Session identifier

        Returns:
            Tuple of (result, reason)
        """
        session = self.get_session(session_id)
        return session.get_result()

    def takeback(self, session_id: str) -> bool:
        """
        悔棋
        Takeback last move

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        return session.takeback()

    def set_pgn_players(self, session_id: str, white: str, black: str) -> None:
        """
        设置对弈者
        Set players

        Args:
            session_id: Session identifier
            white: White player name
            black: Black player name
        """
        session = self.get_session(session_id)
        session.set_pgn_tag("White", white)
        session.set_pgn_tag("Black", black)

    def set_pgn_event(self, session_id: str, event: str, site: str = "?") -> None:
        """
        设置比赛信息
        Set event information

        Args:
            session_id: Session identifier
            event: Event name
            site: Event location
        """
        session = self.get_session(session_id)
        session.set_pgn_tag("Event", event)
        session.set_pgn_tag("Site", site)

    def reset_session(self, session_id: str, starting_fen: Optional[str] = None) -> None:
        """
        重置会话
        Reset session

        Args:
            session_id: Session identifier
            starting_fen: New starting position
        """
        session = self.get_session(session_id)
        session.reset(starting_fen)

    def list_sessions(self) -> list[str]:
        """
        列出所有活跃会话
        List all active sessions

        Returns:
            List of session IDs
        """
        return list(self._active_sessions.keys())
