from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.application.interfaces.unit_of_work import AuthUnitOfWork
from app.features.auth.infrastructure.persistence.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)


class SQLAlchemyUnitOfWork(AuthUnitOfWork):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = SQLAlchemyUserRepository(session)

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, instance: Any) -> None:
        await self._session.refresh(instance)

