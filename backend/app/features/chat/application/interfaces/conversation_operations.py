from abc import ABC, abstractmethod
import uuid

from app.features.chat.application.models import ConversationContext


class ConversationOperations(ABC):
    """Application interface for conversation operations required by Chat."""

    @abstractmethod
    async def get_chat_context(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationContext:
        """Validate ownership/access and return conversation context metadata."""
        ...

    @abstractmethod
    async def update_generated_metadata(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
        summary: str | None = None,
        slug: str | None = None,
    ) -> None:
        """Update AI-generated metadata on the conversation."""
        ...

