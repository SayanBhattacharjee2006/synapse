from abc import ABC, abstractmethod
import uuid


class ConversationOperations(ABC):

    @abstractmethod
    async def validate_ownership(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Validate that a conversation exists, is active, and is owned by the user."""
        raise NotImplementedError

    @abstractmethod
    async def set_document_count(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, count: int
    ) -> None:
        """Idempotently set the document count for a conversation to an absolute value."""
        raise NotImplementedError

    @abstractmethod
    async def adjust_document_count(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, delta: int
    ) -> None:
        """Increment or decrement the document count metadata for a conversation (legacy)."""
        raise NotImplementedError
