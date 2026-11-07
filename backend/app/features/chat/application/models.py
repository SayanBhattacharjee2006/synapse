from dataclasses import dataclass
from typing import Any
import uuid


@dataclass
class ChatEvent:
    """Normalized application-level event emitted during chat execution."""

    event_type: str
    data: Any


@dataclass
class ConversationContext:
    """Context metadata about a conversation required by the chat module."""

    conversation_id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    document_count: int
    has_uploaded_documents: bool

