from abc import ABC, abstractmethod
from typing import AsyncIterator
import uuid

from app.features.chat.application.models import ChatEvent


class ChatEngine(ABC):
    """Application interface for AI chat generation."""

    @abstractmethod
    def stream_chat(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        has_uploaded_documents: bool,
    ) -> AsyncIterator[ChatEvent]:
        """Stream normalized ChatEvents from the AI execution."""
        ...

    @abstractmethod
    async def generate_title(self, content: str) -> str:
        """Generate a short title (maximum 5 words) for the conversation based on message content."""
        ...

