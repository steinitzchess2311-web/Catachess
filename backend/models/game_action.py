"""
GameAction ORM model

Stores ordered game actions to reconstruct game state.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base


class GameAction(Base):
    """
    Game action table.

    Each row represents a state-changing action in a game (move, variation, comment, etc.).
    """
    __tablename__ = "game_actions"
    __table_args__ = (
        UniqueConstraint("game_id", "sequence", name="uq_game_actions_game_sequence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.game_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    action_type: Mapped[str] = mapped_column(String(50), nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<GameAction game_id={self.game_id} seq={self.sequence} type={self.action_type}>"
