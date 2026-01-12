from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from workspace.db.tables.notification_preferences import NotificationPreference


class NotificationPreferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: str) -> NotificationPreference | None:
        result = await self.session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str | NotificationPreference, **kwargs) -> NotificationPreference:
        if isinstance(user_id, NotificationPreference):
            pref = user_id
        else:
            pref = NotificationPreference(
                id=str(ULID()),
                user_id=user_id,
                preferences=kwargs.get("preferences", {}),
                digest_frequency=kwargs.get("digest_frequency", "instant"),
                quiet_hours=kwargs.get("quiet_hours", {}),
                muted_objects=kwargs.get("muted_objects", []),
                enabled=kwargs.get("enabled", True),
            )
        self.session.add(pref)
        await self.session.flush()
        return pref

    async def update(self, pref: NotificationPreference, **kwargs) -> NotificationPreference:
        if "preferences" in kwargs:
            pref.preferences = kwargs["preferences"]
        if "digest_frequency" in kwargs:
            pref.digest_frequency = kwargs["digest_frequency"]
        if "quiet_hours" in kwargs:
            pref.quiet_hours = kwargs["quiet_hours"]
        if "muted_objects" in kwargs:
            pref.muted_objects = kwargs["muted_objects"]
        if "enabled" in kwargs:
            pref.enabled = kwargs["enabled"]

        await self.session.flush()
        return pref

    async def get_or_create_default(self, user_id: str) -> NotificationPreference:
        """Get existing preferences or create default ones."""
        pref = await self.get_by_user_id(user_id)
        if not pref:
            pref = await self.create(user_id)
        return pref
