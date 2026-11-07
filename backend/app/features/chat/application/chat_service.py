from typing import AsyncIterator
import uuid

from app.core.logging import logger
from app.features.chat.application.exceptions import ConversationNotFoundError
from app.features.chat.application.interfaces.chat_engine import ChatEngine
from app.features.chat.application.interfaces.conversation_operations import (
    ConversationOperations,
)
from app.features.chat.application.models import ChatEvent, ConversationContext


class ChatService:
    """Application service coordinating chat execution and lifecycle."""

    def __init__(
        self,
        chat_engine: ChatEngine,
        conversation_ops: ConversationOperations,
    ) -> None:
        self._chat_engine = chat_engine
        self._conversation_ops = conversation_ops

    async def validate_access(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationContext:
        """Validate conversation ownership and return its context.

        Raises ConversationNotFoundError if nonexistent or unauthorized.
        """
        return await self._conversation_ops.get_chat_context(
            conversation_id, user_id
        )

    async def stream_chat(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> AsyncIterator[ChatEvent]:
        """Stream normalized ChatEvents for the user's message."""
        try:
            context = await self.validate_access(conversation_id, user_id)
        except ConversationNotFoundError:
            raise

        needs_title = not bool(context.title and context.title.strip())
        summary: str | None = None
        retrieval_event: ChatEvent | None = None
        web_event: ChatEvent | None = None

        try:
            async for event in self._chat_engine.stream_chat(
                conversation_id=conversation_id,
                user_id=user_id,
                content=content,
                has_uploaded_documents=context.has_uploaded_documents,
            ):
                if event.event_type == "_summary":
                    if isinstance(event.data, dict):
                        summary = event.data.get("summary")
                    elif isinstance(event.data, str):
                        summary = event.data
                elif event.event_type == "retrieval_found":
                    retrieval_event = event
                elif event.event_type == "web_found":
                    web_event = event
                else:
                    yield event

            # Handle first-message title generation and conversation metadata update
            if needs_title:
                try:
                    raw_title = await self._chat_engine.generate_title(content)
                    if raw_title and raw_title.strip():
                        title = raw_title.strip().strip('"').strip("'")
                        slug = title.lower().replace(" ", "-")
                        await self._conversation_ops.update_generated_metadata(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            title=title,
                            summary=summary,
                            slug=slug,
                        )
                        yield ChatEvent(
                            event_type="title", data={"title": title}
                        )
                except Exception:
                    logger.bind(
                        conversation_id=str(conversation_id),
                        user_id=str(user_id),
                    ).exception("chat.title_generation.failed")
                    # Failed title generation must not invalidate the AI response.
                    # Retain summary if available and allow future retries.
                    if summary:
                        try:
                            await self._conversation_ops.update_generated_metadata(
                                conversation_id=conversation_id,
                                user_id=user_id,
                                summary=summary,
                            )
                        except Exception:
                            logger.exception("chat.summary_update.failed")
            elif summary:
                try:
                    await self._conversation_ops.update_generated_metadata(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        summary=summary,
                    )
                except Exception:
                    logger.exception("chat.summary_update.failed")

            if retrieval_event is not None:
                yield retrieval_event

            if web_event is not None:
                yield web_event

            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                summary_updated=bool(summary),
                title_generated=needs_title,
            ).info("chat.response.stream.completed")

        except Exception:
            logger.bind(
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error_reason="exception",
            ).exception("chat.response.stream.failed")

            yield ChatEvent(
                event_type="error",
                data={
                    "status": "error",
                    "message": "Something went wrong while processing your request.",
                },
            )

        yield ChatEvent(event_type="done", data="[DONE]")

