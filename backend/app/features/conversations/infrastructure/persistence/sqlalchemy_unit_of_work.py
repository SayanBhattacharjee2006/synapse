from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.conversations.application.interfaces.unit_of_work import (
    ConversationsUnitOfWork,
)
from app.features.conversations.infrastructure.persistence.sqlalchemy_conversation_repository import (
    SQLAlchemyConversationRepository,
)
from app.features.conversations.infrastructure.persistence.sqlalchemy_message_repository import (
    SQLAlchemyMessageRepository,
)


class SQLAlchemyConversationsUnitOfWork(ConversationsUnitOfWork):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.conversations = SQLAlchemyConversationRepository(session)
        self.messages = SQLAlchemyMessageRepository(session)

    async def __aenter__(self) -> "SQLAlchemyConversationsUnitOfWork":
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

