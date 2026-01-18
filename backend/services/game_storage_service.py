"""
Game Storage Service

Handles game PGN generation with variations and R2 storage.

IMPORTANT: This service handles ALL game logic:
- PGN generation using a variation tree
- Move validation and application
- Variation branches
- R2 storage

The frontend only triggers events, all logic is here.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from core.chess_basic.types import Square, Move, BoardState
from core.chess_basic.constants import Color, PieceType
from core.chess_basic.pgn.common.pgn_types import NAG_SYMBOLS
from core.chess_basic.rule.api import is_legal_move, apply_move
from core.chess_basic.utils.fen import board_to_fen, parse_fen, get_starting_position
from core.chess_basic.utils.san import move_to_san  # SAN conversion
from services.pgn_game_tree import PgnGameTree
from storage.core.client import StorageClient
from storage.core.config import StorageConfig
from storage.core.errors import ObjectNotFound
from models.game import Game


class GameSession:
    """
    In-memory game session with PGN tree

    Each active game has a session that manages:
    - Variation tree for generating PGN with variations
    - Current board state
    - Move history
    """

    def __init__(self, game_id: str, user_id: str):
        self.game_id = game_id
        self.user_id = user_id
        self.state: BoardState = get_starting_position()
        self.start_fen = board_to_fen(self.state)
        self.pgn_tree = PgnGameTree(self.start_fen, {})
        self.move_count = 0
        self._force_variation = False
        self._last_node = None

        # Set default PGN tags
        self.pgn_tree.set_tag("Event", "Casual Game")
        self.pgn_tree.set_tag("Site", "Catachess")
        self.pgn_tree.set_tag("Date", datetime.utcnow().strftime("%Y.%m.%d"))
        self.pgn_tree.set_tag("White", "Player")
        self.pgn_tree.set_tag("Black", "Player")
        self.pgn_tree.set_tag("Result", "*")

    def add_move(
        self,
        move: Move,
        position_fen: Optional[str],
        is_variation: bool,
        parent_move_id: Optional[str],
        move_id: Optional[str],
        comment: Optional[str] = None,
        nag: Optional[int] = None,
    ) -> tuple[bool, BoardState]:
        """
        Add move to game

        Returns:
            (success, new_state)
        """
        # Validate move
        state_before = self.state
        if position_fen:
            state_before = parse_fen(position_fen)

        if not is_legal_move(state_before, move):
            return False, self.state

        # Get SAN notation before applying move
        # Detect if it's a capture for SAN formatting
        target_piece = state_before.get_piece(move.to_square)
        is_capture = target_piece is not None
        san = move_to_san(move, state_before, is_capture=is_capture)

        # Apply move to get new state
        new_state = apply_move(state_before, move)

        # Add to PGN tree
        new_fen = board_to_fen(new_state)
        if position_fen and position_fen != board_to_fen(self.state):
            is_variation = True
        if self._force_variation:
            is_variation = True

        node = self.pgn_tree.add_move(
            position_fen=position_fen or self.start_fen,
            new_fen=new_fen,
            move_uci=move.to_uci(),
            san=san,
            move_number=state_before.fullmove_number,
            color="white" if state_before.turn == Color.WHITE else "black",
            move_id=move_id,
            parent_move_id=parent_move_id,
            comment=comment,
            nag=nag,
        )
        self._last_node = node

        # Add comment if provided
        self.state = new_state
        self.move_count = self.pgn_tree.mainline_count()

        return True, new_state

    def start_variation(self):
        """Start a variation branch"""
        self._force_variation = True

    def end_variation(self):
        """End current variation branch"""
        self._force_variation = False

    def add_comment(self, comment: str):
        """Add comment to last move"""
        if self._last_node:
            self._last_node.comment = comment

    def add_nag(self, nag: int):
        """Add NAG annotation to last move"""
        if self._last_node:
            symbol = NAG_SYMBOLS.get(nag)
            if symbol:
                self._last_node.nag = symbol

    def to_pgn(self) -> str:
        """Generate full PGN string"""
        return self.pgn_tree.to_pgn()

    def get_fen(self) -> str:
        """Get current position FEN"""
        return board_to_fen(self.state)


class GameStorageService:
    """
    Game Storage Service

    Manages game sessions, PGN generation, and R2 storage.
    """

    def __init__(self):
        """Initialize service with R2 client"""
        try:
            config = StorageConfig.from_env()
            self.storage_client = StorageClient(config)
        except ValueError as e:
            # R2 not configured - storage operations will fail
            # This is OK for development without R2
            self.storage_client = None
            print(f"Warning: R2 storage not configured: {e}")

        # In-memory session cache (game_id -> GameSession)
        self.sessions: dict[str, GameSession] = {}

    def get_or_create_session(
        self,
        game_id: str,
        user_id: str,
        db: Session,
    ) -> GameSession:
        """
        Get existing session or create new one

        If game exists in R2, load it. Otherwise create new session.
        """
        # Check cache first
        if game_id in self.sessions:
            return self.sessions[game_id]

        # Try to load from database and R2
        game = db.query(Game).filter(Game.game_id == uuid.UUID(game_id)).first()

        if game and self.storage_client:
            # Load PGN from R2
            try:
                pgn_bytes = self.storage_client.get_object(game.r2_key)
                pgn_string = pgn_bytes.decode('utf-8')

                # TODO: Parse PGN and reconstruct session
                # For now, create new session
                session = GameSession(game_id, user_id)
                self.sessions[game_id] = session
                return session

            except ObjectNotFound:
                # R2 object not found, create new session
                pass

        # Create new session
        session = GameSession(game_id, user_id)
        self.sessions[game_id] = session
        return session

    def save_move(
        self,
        game_id: str,
        user_id: str,
        move_data: dict,
        position_fen: str,
        is_variation: bool,
        parent_move_id: Optional[str],
        comment: Optional[str],
        nag: Optional[int],
        move_number: int,
        db: Session,
    ) -> tuple[bool, str, str]:
        """
        Save a move to the game

        Returns:
            (success, move_id, pgn_preview)
        """
        # Get or create session
        session = self.get_or_create_session(game_id, user_id, db)

        # Parse move from frontend format
        move = self._parse_move(move_data)

        move_id = f"move_{move_number}"

        success, new_state = session.add_move(
            move=move,
            position_fen=position_fen,
            is_variation=is_variation,
            parent_move_id=parent_move_id,
            move_id=move_id,
            comment=comment,
            nag=nag,
        )

        if not success:
            return False, "", ""

        # Save to R2 and database
        self._save_to_storage(game_id, user_id, session, db)

        # Generate PGN preview
        pgn_full = session.to_pgn()
        pgn_preview = pgn_full[:100] + ("..." if len(pgn_full) > 100 else "")

        return True, move_id, pgn_preview

    def start_variation(self, game_id: str, user_id: str, db: Session) -> str:
        """Start a variation branch"""
        session = self.get_or_create_session(game_id, user_id, db)
        session.start_variation()
        variation_id = f"var_{session.move_count}"
        return variation_id

    def end_variation(self, game_id: str, user_id: str, db: Session):
        """End current variation branch"""
        session = self.get_or_create_session(game_id, user_id, db)
        session.end_variation()

    def add_comment(
        self,
        game_id: str,
        user_id: str,
        comment: str,
        db: Session,
    ):
        """Add comment to last move"""
        session = self.get_or_create_session(game_id, user_id, db)
        session.add_comment(comment)
        self._save_to_storage(game_id, user_id, session, db)

    def add_nag(
        self,
        game_id: str,
        user_id: str,
        nag: int,
        db: Session,
    ):
        """Add NAG annotation to last move"""
        session = self.get_or_create_session(game_id, user_id, db)
        session.add_nag(nag)
        self._save_to_storage(game_id, user_id, session, db)

    def get_pgn(self, game_id: str, user_id: str, db: Session) -> tuple[str, int]:
        """
        Get full PGN for game

        Returns:
            (pgn_string, move_count)
        """
        session = self.get_or_create_session(game_id, user_id, db)
        return session.to_pgn(), session.move_count

    def get_game_info(
        self,
        game_id: str,
        user_id: str,
        db: Session,
    ) -> Optional[dict]:
        """Get complete game information"""
        game = db.query(Game).filter(
            Game.game_id == uuid.UUID(game_id),
            Game.user_id == uuid.UUID(user_id),
        ).first()

        if not game:
            return None

        session = self.get_or_create_session(game_id, user_id, db)
        pgn = session.to_pgn()

        return {
            "game_id": str(game.game_id),
            "pgn": pgn,
            "move_count": session.move_count,
            "current_position": session.get_fen(),
            "player_white": game.player_white,
            "player_black": game.player_black,
            "result": game.result,
            "created_at": game.created_at,
            "updated_at": game.updated_at,
        }

    def delete_game(
        self,
        game_id: str,
        user_id: str,
        db: Session,
    ) -> bool:
        """Delete game from database and R2"""
        game = db.query(Game).filter(
            Game.game_id == uuid.UUID(game_id),
            Game.user_id == uuid.UUID(user_id),
        ).first()

        if not game:
            return False

        # Delete from R2
        if self.storage_client:
            try:
                self.storage_client.delete_object(game.r2_key)
            except Exception as e:
                print(f"Warning: Failed to delete from R2: {e}")

        # Delete from database
        db.delete(game)
        db.commit()

        # Remove from session cache
        if game_id in self.sessions:
            del self.sessions[game_id]

        return True

    def _parse_move(self, move_data: dict) -> Move:
        """Parse move from frontend format to chess_basic Move"""
        from_square = Square(
            file=move_data["from_square"]["file"],
            rank=move_data["from_square"]["rank"],
        )
        to_square = Square(
            file=move_data["to_square"]["file"],
            rank=move_data["to_square"]["rank"],
        )

        promotion = None
        if move_data.get("promotion"):
            promotion_map = {
                "queen": PieceType.QUEEN,
                "rook": PieceType.ROOK,
                "bishop": PieceType.BISHOP,
                "knight": PieceType.KNIGHT,
            }
            promotion = promotion_map.get(move_data["promotion"].lower())

        return Move(from_square=from_square, to_square=to_square, promotion=promotion)

    def _save_to_storage(
        self,
        game_id: str,
        user_id: str,
        session: GameSession,
        db: Session,
    ):
        """Save game to R2 and update database"""
        # Generate PGN
        pgn_string = session.to_pgn()

        # R2 key: games/{user_id}/{game_id}.pgn
        r2_key = f"games/{user_id}/{game_id}.pgn"

        # Save to R2
        if self.storage_client:
            self.storage_client.put_object(
                key=r2_key,
                content=pgn_string.encode('utf-8'),
                content_type="application/x-chess-pgn",
            )

        # Update or create database record
        game = db.query(Game).filter(Game.game_id == uuid.UUID(game_id)).first()

        if game:
            # Update existing
            game.move_count = session.move_count
            game.current_fen = session.get_fen()
            game.updated_at = datetime.utcnow()
        else:
            # Create new
            game = Game(
                game_id=uuid.UUID(game_id),
                user_id=uuid.UUID(user_id),
                player_white="Player",
                player_black="Player",
                event="Casual Game",
                site="Catachess",
                date=datetime.utcnow(),
                result="*",
                move_count=session.move_count,
                current_fen=session.get_fen(),
                r2_key=r2_key,
            )
            db.add(game)

        db.commit()


# Global service instance
game_storage_service = GameStorageService()
