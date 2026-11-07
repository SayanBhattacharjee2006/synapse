import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.application.interfaces.user_repository import UserRepository
from app.features.auth.infrastructure.persistence.models import User


class SQLAlchemyUserRepository(UserRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.is_deleted == False,
        )
        return (await self._session.scalars(stmt)).one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(
            User.email == email,
            User.is_deleted == False,
        )
        return (await self._session.scalars(stmt)).one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)
        return user

