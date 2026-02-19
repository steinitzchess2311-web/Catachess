from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.workspace.db.base import Base


class User(Base):
    """Minimal read-only view of the shared users table.

    Only maps the columns that actually exist in the table created by the
    main app's User model (id + username). Do NOT add TimestampMixin here —
    the real users table has created_at but no updated_at, so including
    TimestampMixin causes "column updated_at does not exist" on every query.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
