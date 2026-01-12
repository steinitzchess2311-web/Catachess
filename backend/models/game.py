"""
Game ORM model

Stores game metadata in PostgreSQL.
Actual PGN data is stored in R2 storage.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base


class Game(Base):
    """
    Game metadata table

    Stores metadata about chess games. The actual PGN data is stored in R2.
    The r2_key field references the object key in R2 storage.
    """
    __tablename__ = "games"

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Game metadata (from PGN tags)
    player_white: Mapped[str | None] = mapped_column(String(100), nullable=True)
    player_black: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event: Mapped[str | None] = mapped_column(String(200), nullable=True)
    site: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result: Mapped[str] = mapped_column(String(10), nullable=False, default="*")  # "*", "1-0", "0-1", "1/2-1/2"

    # Game progress tracking
    move_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_fen: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # R2 storage reference
    r2_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Game game_id={self.game_id} user={self.user_id} moves={self.move_count}>"
