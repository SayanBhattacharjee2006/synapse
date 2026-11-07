from fastapi import Depends

from app.features.chat.application.chat_service import ChatService
from app.features.chat.wiring import get_chat_service


def get_current_chat_service(
    service: ChatService = Depends(get_chat_service),
) -> ChatService:
    """Dependency helper to resolve ChatService."""
    return service

