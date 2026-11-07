from typing import Any
from fastapi import Depends, Request

from app.features.chat.application.chat_service import ChatService
from app.features.chat.application.interfaces.chat_engine import ChatEngine
from app.features.chat.application.interfaces.conversation_operations import (
    ConversationOperations,
)
from app.features.chat.infrastructure.ai.langgraph_chat_engine import (
    LangGraphChatEngine,
)
from app.features.chat.infrastructure.integrations.conversation_adapter import (
    ConversationAdapter,
)
from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.wiring import get_conversation_service


def get_compiled_graph(request: Request) -> Any:
    """Retrieve the application-scoped compiled LangGraph instance from app state."""
    if hasattr(request.app.state, "graph"):
        return request.app.state.graph
    raise RuntimeError(
        "Application compiled LangGraph instance not found on app.state"
    )


def get_chat_engine(
    graph: Any = Depends(get_compiled_graph),
) -> ChatEngine:
    return LangGraphChatEngine(graph=graph)


def get_conversation_operations(
    conversation_service: ConversationService = Depends(
        get_conversation_service
    ),
) -> ConversationOperations:
    return ConversationAdapter(conversation_service=conversation_service)


def get_chat_service(
    chat_engine: ChatEngine = Depends(get_chat_engine),
    conversation_ops: ConversationOperations = Depends(
        get_conversation_operations
    ),
) -> ChatService:
    return ChatService(
        chat_engine=chat_engine,
        conversation_ops=conversation_ops,
    )

