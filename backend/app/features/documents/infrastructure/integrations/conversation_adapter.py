import uuid
from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.application.exceptions import (
    ConversationNotFoundError,
)
from app.features.documents.application.exceptions import (
    ConversationAccessError,
)
from app.features.documents.application.interfaces.conversation_operations import (
    ConversationOperations,
)


class ConversationAdapter(ConversationOperations):

    def __init__(self, conversation_service: ConversationService) -> None:
        self._conversation_service = conversation_service

    async def validate_ownership(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        try:
            await self._conversation_service.get_conversation(
                conversation_id, user_id
            )
            return True
        except ConversationNotFoundError as e:
            raise ConversationAccessError(
                f"Conversation '{conversation_id}' not found or inaccessible"
            ) from e

    async def adjust_document_count(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, delta: int
    ) -> None:
        try:
            await self._conversation_service.adjust_document_count(
                conversation_id, user_id, delta
            )
        except ConversationNotFoundError as e:
            raise ConversationAccessError(
                f"Failed to adjust document count: conversation '{conversation_id}' not found"
            ) from e

