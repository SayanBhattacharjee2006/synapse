import uuid
from typing import TYPE_CHECKING, Any
from app.core.logging import logger
from app.features.conversations.application.enums import SenderEnum
from app.features.conversations.application.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
)
from app.features.conversations.application.interfaces.unit_of_work import (
    ConversationsUnitOfWork,
)
from app.features.conversations.infrastructure.persistence.models import Message

if TYPE_CHECKING:
    from app.features.conversations.presentation.schemas import MessageCreate


class MessageService:

    def __init__(self, uow: ConversationsUnitOfWork) -> None:
        self._uow = uow

    async def get_messages(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Message]:
        try:
            # Validate that the conversation exists, is active, and belongs to the user
            conversation = await self._uow.conversations.get_by_id_and_user(
                conversation_id, user_id
            )
            if conversation is None:
                logger.bind(
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                    error_reason="conversation_not_found",
                ).warning("message.fetch.failed")
                raise ConversationNotFoundError("Conversation not found")

            return await self._uow.messages.list_by_conversation(
                conversation_id
            )
        except ConversationNotFoundError:
            raise
        except Exception:
            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error_reason="database_error",
            ).exception("message.fetch.error")
            raise

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        data: "MessageCreate | None" = None,
        content: str | None = None,
        sender: SenderEnum | str | None = None,
    ) -> Message:
        try:
            msg_content = content
            msg_sender = sender
            if data is not None:
                msg_content = getattr(data, "content", msg_content)
                msg_sender = getattr(data, "sender", msg_sender)

            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                sender=str(msg_sender),
            ).info("message.create.started")

            conversation = await self._uow.conversations.get_by_id_and_user(
                conversation_id, user_id
            )
            if conversation is None:
                logger.bind(
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                    error_reason="conversation_not_found",
                ).warning("message.create.failed")
                raise ConversationNotFoundError("Conversation not found")

            if msg_content is None or msg_sender is None:
                raise ValueError("Message content and sender must be provided")

            message = Message(
                content=msg_content,
                sender=msg_sender,
                conversation_id=conversation_id,
            )

            await self._uow.messages.create(message)
            await self._uow.commit()
            await self._uow.refresh(message)

            logger.bind(
                conversation_id=str(conversation_id),
                message_id=str(message.id),
                user_id=str(user_id),
            ).info("message.create.completed")
            return message
        except ConversationNotFoundError:
            raise
        except Exception:
            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error_reason="database_error",
            ).exception("message.create.failed")
            await self._uow.rollback()
            raise

    async def delete_message(
        self,
        message_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Message:
        try:
            logger.bind(
                message_id=str(message_id),
                conversation_id=str(conversation_id),
                user_id=str(user_id),
            ).info("message.delete.started")

            conversation = await self._uow.conversations.get_by_id_and_user(
                conversation_id, user_id
            )
            if conversation is None:
                logger.bind(
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                    error_reason="conversation_not_found",
                ).warning("message.delete.failed")
                raise ConversationNotFoundError("Conversation not found")

            message = await self._uow.messages.get_by_id_and_conversation(
                message_id, conversation_id
            )
            if message is None:
                logger.bind(
                    message_id=str(message_id),
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                    error_reason="message_not_found",
                ).warning("message.delete.failed")
                raise MessageNotFoundError("Message not found")

            await self._uow.messages.soft_delete(message)
            await self._uow.commit()
            await self._uow.refresh(message)

            logger.bind(
                message_id=str(message_id),
                conversation_id=str(conversation_id),
                user_id=str(user_id),
            ).info("message.delete.completed")
            return message
        except (ConversationNotFoundError, MessageNotFoundError):
            raise
        except Exception:
            logger.bind(
                message_id=str(message_id),
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error_reason="database_error",
            ).exception("message.delete.failed")
            await self._uow.rollback()
            raise
