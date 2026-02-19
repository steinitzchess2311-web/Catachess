"""
GroupMember model
=================
Junction table: which users belong to which group, with a role.

Roles (stored as strings):
  'owner'  — creator, one per group, cannot be kicked
  'admin'  — can add/kick members and rename the group
  'member' — can only send messages and leave

'username' is denormalised (copied from users.username at join time)
so the member list stays readable without a cross-DB join.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.catchat.db.session import Base


class GroupMember(Base):
    __tablename__ = "catchat_group_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catchat_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False, default="member")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_catchat_group_member"),
    )
