import uuid
from typing import TYPE_CHECKING, Any
from app.core.logging import logger
from app.features.conversations.application.exceptions import (
    ConversationNotFoundError,
)
from app.features.conversations.application.interfaces.unit_of_work import (
    ConversationsUnitOfWork,
)
from app.features.conversations.infrastructure.persistence.models import (
    Conversation,
)

if TYPE_CHECKING:
    from app.features.conversations.presentation.schemas import ConversationUpdate


class ConversationService:

    def __init__(self, uow: ConversationsUnitOfWork) -> None:
        self._uow = uow

    async def list_conversations(
        self, user_id: uuid.UUID
    ) -> list[Conversation]:
        try:
            return await self._uow.conversations.list_by_user(user_id)
        except Exception:
            logger.bind(
                user_id=str(user_id),
                error_reason="database_error",
            ).exception("conversation.list.error")
            raise

    async def get_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation:
        try:
            conversation = await self._uow.conversations.get_by_id_and_user(
                conversation_id, user_id
            )
            if conversation is None:
                logger.bind(
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                    error_reason="conversation_not_found",
                ).warning("conversation.fetch.error")
                raise ConversationNotFoundError("Conversation not found")
            return conversation
        except ConversationNotFoundError:
            raise
        except Exception:
            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error_reason="database_error",
            ).exception("conversation.fetch.error")
            raise

    async def create_conversation(
        self, user_id: uuid.UUID
    ) -> Conversation:
        try:
            logger.bind(user_id=str(user_id)).info(
                "conversation.create.started"
            )
            new_id = uuid.uuid4()
            conversation = Conversation(
                id=new_id,
                slug=str(new_id),
                user_id=user_id,
            )
            await self._uow.conversations.create(conversation)
            await self._uow.commit()
            await self._uow.refresh(conversation)

            logger.bind(
                conversation_id=str(new_id),
                user_id=str(user_id),
            ).info("conversation.create.completed")
            return conversation
        except Exception:
            logger.bind(
                user_id=str(user_id),
                error_reason="database_error",
            ).exception("conversation.create.failed")
            await self._uow.rollback()
            raise

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        data: "ConversationUpdate | None" = None,
        title: str | None = None,
    ) -> Conversation:
        try:
            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
            ).info("conversation.update.started")

            conversation = await self._uow.conversations.get_by_id_and_user(
                conversation_id, user_id
            )
            if conversation is None:
                logger.bind(
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                    error_reason="conversation_not_found",
                ).warning("conversation.update.failed")
                raise ConversationNotFoundError("Conversation not found")

            if data is not None:
                if hasattr(data, "model_dump"):
                    update_dict = data.model_dump(exclude_unset=True)
                elif isinstance(data, dict):
                    update_dict = data
                else:
                    update_dict = {}
                for field, value in update_dict.items():
                    setattr(conversation, field, value)

            if title is not None:
                conversation.title = title

            await self._uow.conversations.update(conversation)
            await self._uow.commit()
            await self._uow.refresh(conversation)

            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
            ).info("conversation.update.completed")
            return conversation
        except ConversationNotFoundError:
            raise
        except Exception:
            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error_reason="database_error",
            ).exception("conversation.update.failed")
            await self._uow.rollback()
            raise

    async def delete_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation:
        try:
            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
            ).info("conversation.delete.started")

            conversation = await self._uow.conversations.get_by_id_and_user(
                conversation_id, user_id
            )
            if conversation is None:
                logger.bind(
                    conversation_id=str(conversation_id),
                    user_id=str(user_id),
                    error_reason="conversation_not_found",
                ).warning("conversation.delete.failed")
                raise ConversationNotFoundError("Conversation not found")

            async with self._uow:
                await self._uow.conversations.soft_delete(conversation)
                await self._uow.messages.soft_delete_by_conversation(
                    conversation_id
                )
                await self._uow.commit()
                await self._uow.refresh(conversation)

            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                document_count=str(conversation.document_count),
            ).info("conversation.delete.completed")
            return conversation
        except ConversationNotFoundError:
            raise
        except Exception:
            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error_reason="database_error",
            ).exception("conversation.delete.failed")
            await self._uow.rollback()
            raise

    async def update_generated_metadata(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
        summary: str | None = None,
        slug: str | None = None,
    ) -> Conversation:
        conversation = await self._uow.conversations.get_by_id_and_user(
            conversation_id, user_id
        )
        if conversation is None:
            raise ConversationNotFoundError("Conversation not found")

        if title is not None:
            conversation.title = title
        if summary is not None:
            conversation.summary = summary
        if slug is not None:
            conversation.slug = slug

        await self._uow.commit()
        await self._uow.refresh(conversation)
        return conversation

    async def adjust_document_count(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        delta: int,
    ) -> Conversation:
        conversation = await self._uow.conversations.get_by_id_and_user(
            conversation_id, user_id
        )
        if conversation is None:
            raise ConversationNotFoundError("Conversation not found")

        conversation.document_count = max(conversation.document_count + delta, 0)
        await self._uow.commit()
        await self._uow.refresh(conversation)
        return conversation

    async def set_document_count(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        count: int,
    ) -> Conversation:
        conversation = await self._uow.conversations.get_by_id_and_user(
            conversation_id, user_id
        )
        if conversation is None:
            raise ConversationNotFoundError("Conversation not found")

        conversation.document_count = max(count, 0)
        await self._uow.commit()
        await self._uow.refresh(conversation)
        return conversation
