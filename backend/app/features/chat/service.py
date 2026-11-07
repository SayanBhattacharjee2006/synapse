from typing import AsyncIterator
import uuid
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.chat.application.chat_service import ChatService
from app.features.chat.infrastructure.ai.langgraph_chat_engine import (
    LangGraphChatEngine,
    STATUS_BY_NODE,
)
from app.features.chat.infrastructure.integrations.conversation_adapter import (
    ConversationAdapter,
)
from app.features.chat.presentation.schemas import ChatRequest
from app.features.chat.presentation.streaming import format_sse_stream
from app.features.chat.wiring import get_chat_service
from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyConversationsUnitOfWork,
)


async def stream_chat(
    request: Request,
    conversation_id: uuid.UUID,
    message: ChatRequest,
    db: AsyncSession,
    user_id: uuid.UUID,
) -> AsyncIterator[str]:
    """Backward compatibility wrapper for legacy stream_chat callers."""
    uow = SQLAlchemyConversationsUnitOfWork(db)
    conv_service = ConversationService(uow=uow)
    conv_adapter = ConversationAdapter(conversation_service=conv_service)
    chat_engine = LangGraphChatEngine(graph=request.app.state.graph)
    service = ChatService(
        chat_engine=chat_engine, conversation_ops=conv_adapter
    )

    event_stream = service.stream_chat(
        conversation_id=conversation_id,
        user_id=user_id,
        content=message.content,
    )
    async for chunk in format_sse_stream(event_stream):
        yield chunk


__all__ = ["ChatService", "stream_chat", "get_chat_service", "STATUS_BY_NODE"]
