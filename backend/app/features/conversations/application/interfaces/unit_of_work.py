from abc import ABC, abstractmethod
from typing import Any
from app.features.conversations.application.interfaces.conversation_repository import (
    ConversationRepository,
)
from app.features.conversations.application.interfaces.message_repository import (
    MessageRepository,
)


class ConversationsUnitOfWork(ABC):
    conversations: ConversationRepository
    messages: MessageRepository

    @abstractmethod
    async def __aenter__(self) -> "ConversationsUnitOfWork":
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        """Commit the active transaction."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the active transaction."""
        raise NotImplementedError

    @abstractmethod
    async def refresh(self, instance: Any) -> None:
        """Refresh instance state from the database."""
        raise NotImplementedError

