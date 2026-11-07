import uuid

from app.features.chat.application.exceptions import (
    ConversationNotFoundError,
)
from app.features.chat.application.interfaces.conversation_operations import (
    ConversationOperations,
)
from app.features.chat.application.models import ConversationContext
from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.application.exceptions import (
    ConversationNotFoundError as ServiceConversationNotFoundError,
)


class ConversationAdapter(ConversationOperations):
    """Adapter implementing ConversationOperations using the Conversations module's application service."""

    def __init__(self, conversation_service: ConversationService) -> None:
        self._conversation_service = conversation_service

    async def get_chat_context(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationContext:
        try:
            conv = await self._conversation_service.get_conversation(
                conversation_id, user_id
            )
            return ConversationContext(
                conversation_id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                document_count=conv.document_count,
                has_uploaded_documents=(conv.document_count > 0),
            )
        except ServiceConversationNotFoundError as e:
            raise ConversationNotFoundError(
                f"Conversation '{conversation_id}' not found or inaccessible"
            ) from e

    async def update_generated_metadata(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
        summary: str | None = None,
        slug: str | None = None,
    ) -> None:
        try:
            await self._conversation_service.update_generated_metadata(
                conversation_id=conversation_id,
                user_id=user_id,
                title=title,
                summary=summary,
                slug=slug,
            )
        except ServiceConversationNotFoundError as e:
            raise ConversationNotFoundError(
                f"Conversation '{conversation_id}' not found or inaccessible"
            ) from e

