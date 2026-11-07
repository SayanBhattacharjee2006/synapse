from abc import ABC, abstractmethod
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.features.conversations.infrastructure.persistence.models import Conversation


class ConversationRepository(ABC):

    @abstractmethod
    async def get_by_id(self, conversation_id: uuid.UUID) -> "Conversation | None":
        """Retrieve an active (non-deleted) conversation by its ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_and_user(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> "Conversation | None":
        """Retrieve an active conversation by ID that belongs to the given user."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(self, user_id: uuid.UUID) -> list["Conversation"]:
        """List all active conversations for a user ordered by creation date descending."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, conversation: "Conversation") -> "Conversation":
        """Add a conversation to persistence (without committing)."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, conversation: "Conversation") -> "Conversation":
        """Mark or track updates on a conversation."""
        raise NotImplementedError

    @abstractmethod
    async def soft_delete(self, conversation: "Conversation") -> None:
        """Mark a conversation as deleted."""
        raise NotImplementedError

