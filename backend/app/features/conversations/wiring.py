from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.application.interfaces.unit_of_work import (
    ConversationsUnitOfWork,
)
from app.features.conversations.application.message_service import (
    MessageService,
)
from app.features.conversations.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyConversationsUnitOfWork,
)


def get_conversations_uow(
    session: AsyncSession = Depends(get_db),
) -> ConversationsUnitOfWork:
    return SQLAlchemyConversationsUnitOfWork(session)


def get_conversation_service(
    uow: ConversationsUnitOfWork = Depends(get_conversations_uow),
) -> ConversationService:
    return ConversationService(uow=uow)


def get_message_service(
    uow: ConversationsUnitOfWork = Depends(get_conversations_uow),
) -> MessageService:
    return MessageService(uow=uow)

