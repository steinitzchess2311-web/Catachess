"""
Game Storage Service

Handles game PGN generation with variations and R2 storage.

IMPORTANT: This service handles ALL game logic:
- PGN generation using chess_basic.pgn.vari.writer
- Move validation and application
- Variation branches
- R2 storage

The frontend only triggers events, all logic is here.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from core.chess_basic.types import Square, Move, BoardState, Piece
from core.chess_basic.constants import Color, PieceType
from core.chess_basic.pgn.vari import PGNWriterVari
from core.chess_basic.rule.api import is_legal_move, apply_move, generate_legal_moves
from core.chess_basic.utils.san import move_to_san  # SAN conversion
from storage.core.client import StorageClient
from storage.core.config import StorageConfig
from storage.core.errors import ObjectNotFound
from models.game import Game


class GameSession:
    """
    In-memory game session with PGN writer

    Each active game has a session that manages:
    - PGNWriterVari for generating PGN with variations
    - Current board state
    - Move history
    """

    def __init__(self, game_id: str, user_id: str):
        self.game_id = game_id
        self.user_id = user_id
        self.writer = PGNWriterVari()
        self.state: BoardState = BoardState.initial()  # Start position
        self.move_count = 0
        self.in_variation = False

        # Set default PGN tags
        self.writer.set_tag("Event", "Casual Game")
        self.writer.set_tag("Site", "Catachess")
        self.writer.set_tag("Date", datetime.utcnow().strftime("%Y.%m.%d"))
        self.writer.set_tag("White", "Player")
        self.writer.set_tag("Black", "Player")
        self.writer.set_tag("Result", "*")

    def add_move(
        self,
        move: Move,
        comment: Optional[str] = None,
        nag: Optional[int] = None,
    ) -> tuple[bool, BoardState]:
        """
        Add move to game

        Returns:
            (success, new_state)
        """
        # Validate move
        if not is_legal_move(self.state, move):
            return False, self.state

        # Get SAN notation before applying move
        # Detect if it's a capture for SAN formatting
        target_piece = self.state.get_piece(move.to_square)
        is_capture = target_piece is not None
        san = move_to_san(move, self.state, is_capture=is_capture)

        # Apply move to get new state
        new_state = apply_move(self.state, move)

        # Add to PGN writer
        self.writer.add_move(move, self.state, san)

        # Add comment if provided
        if comment:
            self.writer.add_comment(comment)

        # Add NAG if provided
        if nag:
            self.writer.add_nag(nag)

        # Update state
        self.state = new_state
        self.move_count += 1

        return True, new_state

    def start_variation(self):
        """Start a variation branch"""
        self.writer.start_variation()
        self.in_variation = True

    def end_variation(self):
        """End current variation branch"""
        self.writer.end_variation()
        self.in_variation = False

    def add_comment(self, comment: str):
        """Add comment to last move"""
        self.writer.add_comment(comment)

    def add_nag(self, nag: int):
        """Add NAG annotation to last move"""
        self.writer.add_nag(nag)

    def to_pgn(self) -> str:
        """Generate full PGN string"""
        return self.writer.to_pgn_string()

    def get_fen(self) -> str:
        """Get current position FEN"""
        return self.state.to_fen()


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

        # Add move to session
        success, new_state = session.add_move(move, comment, nag)

        if not success:
            return False, "", ""

        # Generate move ID
        move_id = f"move_{move_number}"

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
        variation_id = f"var_{len(session.writer._stack._stack)}"
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
