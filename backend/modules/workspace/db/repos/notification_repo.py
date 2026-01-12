from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.notifications import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, notification: Notification) -> Notification:
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def get_by_id(self, notification_id: str) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_unread(self, user_id: str) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_unread_since(
        self, user_id: str, since: datetime
    ) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
                Notification.created_at >= since,
            )
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_as_read(self, notification_id: str) -> bool:
        result = await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read_at=datetime.now(UTC))
        )
        await self.session.flush()
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: str) -> int:
        result = await self.session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        )
        await self.session.flush()
        return result.rowcount

    async def delete_notification(self, notification_id: str) -> bool:
        result = await self.session.execute(
            delete(Notification).where(Notification.id == notification_id)
        )
        await self.session.flush()
        return result.rowcount > 0
