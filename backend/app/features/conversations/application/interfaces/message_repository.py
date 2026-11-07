from abc import ABC, abstractmethod
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.features.conversations.infrastructure.persistence.models import Message


class MessageRepository(ABC):

    @abstractmethod
    async def get_by_id(self, message_id: uuid.UUID) -> "Message | None":
        """Retrieve an active message by its ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_and_conversation(
        self, message_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> "Message | None":
        """Retrieve an active message by ID belonging to a specific conversation."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_conversation(
        self, conversation_id: uuid.UUID
    ) -> list["Message"]:
        """List active messages belonging to a conversation ordered by created_at ascending."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, message: "Message") -> "Message":
        """Add a message to persistence (without committing)."""
        raise NotImplementedError

    @abstractmethod
    async def soft_delete(self, message: "Message") -> None:
        """Mark a single message as deleted."""
        raise NotImplementedError

    @abstractmethod
    async def soft_delete_by_conversation(
        self, conversation_id: uuid.UUID
    ) -> int:
        """Mark all messages belonging to a conversation as deleted."""
        raise NotImplementedError

