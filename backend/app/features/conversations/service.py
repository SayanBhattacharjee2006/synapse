import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.application.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
)
from app.features.conversations.application.message_service import (
    MessageService,
)
from app.features.conversations.infrastructure.persistence.models import (
    Conversation,
    Message,
)
from app.features.conversations.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyConversationsUnitOfWork,
)
from app.features.conversations.presentation.schemas import (
    ConversationUpdate,
    MessageCreate,
)


def _create_conversation_service(db: AsyncSession) -> ConversationService:
    return ConversationService(uow=SQLAlchemyConversationsUnitOfWork(db))


def _create_message_service(db: AsyncSession) -> MessageService:
    return MessageService(uow=SQLAlchemyConversationsUnitOfWork(db))


async def get_all_conversations(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Conversation]:
    service = _create_conversation_service(db)
    return await service.list_conversations(user_id)


async def get_conversation_by_id(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    service = _create_conversation_service(db)
    try:
        return await service.get_conversation(conversation_id, user_id)
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


async def create_conversations(
    db: AsyncSession, user_id: uuid.UUID
) -> Conversation:
    service = _create_conversation_service(db)
    return await service.create_conversation(user_id)


async def update_conversations(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    user_id: uuid.UUID,
) -> Conversation:
    service = _create_conversation_service(db)
    try:
        return await service.update_conversation(conversation_id, user_id, data)
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


async def delete_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    service = _create_conversation_service(db)
    try:
        return await service.delete_conversation(conversation_id, user_id)
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


async def get_messages(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> list[Message]:
    service = _create_message_service(db)
    try:
        return await service.get_messages(conversation_id, user_id)
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


async def create_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    data: MessageCreate,
    user_id: uuid.UUID,
) -> Message:
    service = _create_message_service(db)
    try:
        return await service.create_message(conversation_id, user_id, data)
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


async def delete_message(
    db: AsyncSession,
    message_id: uuid.UUID,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Message:
    service = _create_message_service(db)
    try:
        return await service.delete_message(
            message_id, conversation_id, user_id
        )
    except (ConversationNotFoundError, MessageNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


__all__ = [
    "get_all_conversations",
    "get_conversation_by_id",
    "create_conversations",
    "update_conversations",
    "delete_conversation",
    "get_messages",
    "create_message",
    "delete_message",
]
