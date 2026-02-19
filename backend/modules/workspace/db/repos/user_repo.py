from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace.db.tables.users import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def search_by_username(self, query: str, limit: int = 10) -> list[User]:
        result = await self.session.execute(
            select(User)
            .where(User.username.ilike(f"%{query}%"))
            .order_by(User.username)
            .limit(limit)
        )
        return list(result.scalars().all())
