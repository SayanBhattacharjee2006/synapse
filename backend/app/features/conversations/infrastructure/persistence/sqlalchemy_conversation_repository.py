import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.conversations.application.interfaces.conversation_repository import (
    ConversationRepository,
)
from app.features.conversations.infrastructure.persistence.models import Conversation


class SQLAlchemyConversationRepository(ConversationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False,
        )
        return (await self._session.scalars(stmt)).one_or_none()

    async def get_by_id_and_user(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False,
            Conversation.user_id == user_id,
        )
        return (await self._session.scalars(stmt)).one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,
            )
            .order_by(Conversation.created_at.desc())
        )
        return list((await self._session.scalars(stmt)).all())

    async def create(self, conversation: Conversation) -> Conversation:
        self._session.add(conversation)
        return conversation

    async def update(self, conversation: Conversation) -> Conversation:
        return conversation

    async def soft_delete(self, conversation: Conversation) -> None:
        conversation.is_deleted = True

