import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.conversations.application.interfaces.message_repository import (
    MessageRepository,
)
from app.features.conversations.infrastructure.persistence.models import Message


class SQLAlchemyMessageRepository(MessageRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, message_id: uuid.UUID) -> Message | None:
        stmt = select(Message).where(
            Message.id == message_id,
            Message.is_deleted == False,
        )
        return (await self._session.scalars(stmt)).one_or_none()

    async def get_by_id_and_conversation(
        self, message_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Message | None:
        stmt = select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conversation_id,
            Message.is_deleted == False,
        )
        return (await self._session.scalars(stmt)).one_or_none()

    async def list_by_conversation(
        self, conversation_id: uuid.UUID
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False,
            )
            .order_by(Message.created_at)
        )
        return list((await self._session.scalars(stmt)).all())

    async def create(self, message: Message) -> Message:
        self._session.add(message)
        return message

    async def soft_delete(self, message: Message) -> None:
        message.is_deleted = True

    async def soft_delete_by_conversation(
        self, conversation_id: uuid.UUID
    ) -> int:
        stmt = (
            update(Message)
            .where(Message.conversation_id == conversation_id)
            .values(is_deleted=True)
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

