import uuid
from fastapi import HTTPException
from sqlalchemy import select, update
from app.features.conversations.models import Conversation, Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.conversations.schemas import ConversationUpdate, MessageCreate
from app.core.logging import logger

# Conversation Services


async def get_all_conversations(db: AsyncSession, user_id: uuid.UUID):

    try:
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
        ).order_by(Conversation.created_at.desc())

        conversations = (await db.scalars(stmt)).all()
    except Exception:
        logger.bind(
            user_id = str(user_id),
            error_reason="database_error",
        ).exception("conversation.list.error")
        raise 

    return conversations


async def get_conversation_by_id(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
):
    try:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False,
            Conversation.user_id == user_id,
        )

        conversation = (await db.scalars(stmt)).one_or_none()

        if conversation is None:
            logger.bind(
                conversation_id = str(conversation_id),
                user_id = str(user_id),
                error_reason="conversation_not_found",
            ).warning("conversation.fetch.error")
            raise HTTPException(status_code=404, detail="Conversation not found")

    except HTTPException:
        raise
        
    except Exception:
        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id),
            error_reason="database_error",
        ).exception("conversation.fetch.error")
        raise 

    return conversation


async def create_conversations(db: AsyncSession, user_id: uuid.UUID):

    try:
        logger.bind(
            user_id = str(user_id)
        ).info("conversation.create.started")

        new_id = uuid.uuid4()

        conversation = Conversation(
            id=new_id,
            slug=str(new_id),
            user_id=user_id,
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        logger.bind(
            conversation_id = str(new_id),
            user_id = str(user_id)
        ).info("conversation.create.completed")

    except Exception:
        logger.bind(
            user_id = str(user_id),
            error_reason="database_error",
        ).exception("conversation.create.failed")

        await db.rollback()
        raise 

    return conversation


async def update_conversations(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    user_id: uuid.UUID,
):

    try:

        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id)
        ).info("conversation.update.started")

        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False,
            Conversation.user_id == user_id,
        )

        conversation = (await db.scalars(stmt)).one_or_none()

        if conversation is None:
            logger.bind(
                conversation_id = str(conversation_id),
                user_id = str(user_id),
                error_reason="conversation_not_found",
            ).warning("conversation.update.failed")
            raise HTTPException(status_code=404, detail="Conversation not found")

        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(conversation, field, value)

        await db.commit()
        await db.refresh(conversation)

        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id)
        ).info("conversation.update.completed")

    except HTTPException:
        raise

    except Exception:
        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id),
            error_reason="database_error",
        ).exception("conversation.update.failed")

        await db.rollback()
        raise 

    return conversation


async def delete_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
):
    try:

        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id)
        ).info("conversation.delete.started")

        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False,
            Conversation.user_id == user_id,
        )

        conversation = (await db.scalars(stmt)).one_or_none()

        if conversation is None:
            logger.bind(
                conversation_id = str(conversation_id),
                user_id = str(user_id),
                error_reason="conversation_not_found",
            ).warning("conversation.delete.failed")

            raise HTTPException(status_code=404, detail="Conversation not found")

        setattr(conversation, "is_deleted", True)

        await db.execute(
            update(Message)
            .where(Message.conversation_id == conversation_id)
            .values(is_deleted=True)
        )

        await db.commit()
        await db.refresh(conversation)

        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id),
            document_count = str(conversation.document_count),
        ).info("conversation.delete.completed")

    except HTTPException:
        raise

    except Exception:
        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id),
            error_reason="database_error",
        ).exception("conversation.delete.failed")

        await db.rollback()
        raise 
    
    return conversation


# Message Services


async def get_messages(db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID):

    try:
        stmt = (
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(Message.conversation_id == conversation_id, Message.is_deleted == False, Conversation.user_id == user_id, Conversation.is_deleted == False)
            .order_by(Message.created_at)
        )

        messages = (await db.scalars(stmt)).all()
    except Exception:
        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id),
            error_reason="database_error",
        ).exception("message.fetch.error")
        raise
    return messages


async def delete_message(
    db: AsyncSession, message_id: uuid.UUID, conversation_id: uuid.UUID, user_id: uuid.UUID
):

    try:
        logger.bind(
            message_id = str(message_id),
            conversation_id = str(conversation_id),
            user_id = str(user_id),
        ).info("message.delete.started")

        stmt = select(Message).join(Conversation, Conversation.id == Message.conversation_id).where(
            Message.conversation_id == conversation_id,
            Message.id == message_id,
            Message.is_deleted == False,
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
        )

        message = (await db.scalars(stmt)).one_or_none()

        if message is None:
            logger.bind(
                message_id = str(message_id),
                conversation_id = str(conversation_id),
                user_id = str(user_id),
                error_reason="message_not_found",
            ).warning("message.delete.failed")
            raise HTTPException(status_code=404, detail="Message not found")

        setattr(message, "is_deleted", True)

        await db.commit()
        await db.refresh(message)

        logger.bind(
            message_id = str(message_id),
            conversation_id = str(conversation_id),
            user_id = str(user_id),
        ).info("message.delete.completed")

    except HTTPException:
        raise

    except Exception:
        logger.bind(
            message_id = str(message_id),
            conversation_id = str(conversation_id),
            user_id = str(user_id),
            error_reason="database_error",
        ).exception("message.delete.failed")
        await db.rollback()
        raise

    return message


async def create_message(
    db: AsyncSession, conversation_id: uuid.UUID, data: MessageCreate, user_id: uuid.UUID
):
    try:

        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id),
            sender = str(data.sender),
        ).info("message.create.started")

        stmt = select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id ,Conversation.is_deleted == False)

        conversation = (await db.scalars(stmt)).one_or_none()

        if conversation is None:
            logger.bind(
                conversation_id = str(conversation_id),
                user_id = str(user_id),
                error_reason="conversation_not_found",
            ).warning("message.create.failed")
            raise HTTPException(status_code=404, detail="Conversation not found")

        message = Message(
            content=data.content, sender=data.sender, conversation_id=conversation_id
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        logger.bind(
            conversation_id = str(conversation_id),
            message_id = str(message.id),
            user_id = str(user_id),
        ).info("message.create.completed")

    except HTTPException:
        raise

    except Exception:
        logger.bind(
            conversation_id = str(conversation_id),
            user_id = str(user_id),
            error_reason="database_error",
        ).exception("message.create.failed")
        await db.rollback()
        raise

    return message
