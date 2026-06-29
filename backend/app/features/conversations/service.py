import uuid
from sqlalchemy import select, update
from app.features.conversations.models import Conversation, Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.conversations.schemas import ConversationUpdate, MessageCreate
from app.ai.rag.services.conversations_memory_service import store_message

# Conversation Services


async def get_all_conversations(db: AsyncSession, user_id: uuid.UUID):

    stmt = select(Conversation).where(
        Conversation.user_id == user_id,
        Conversation.is_deleted == False,
    ).order_by(Conversation.created_at.desc())

    conversations = (await db.scalars(stmt)).all()
    return conversations


async def get_conversation_by_id(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
):
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.is_deleted == False,
        Conversation.user_id == user_id,
    )

    conversation = (await db.scalars(stmt)).one_or_none()

    if conversation is None:
        raise ValueError("Conversation not found")

    return conversation


async def create_conversations(db: AsyncSession, user_id: uuid.UUID):

    new_id = uuid.uuid4()

    conversation = Conversation(
        id=new_id,
        slug=str(new_id),
        user_id=user_id,
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation


async def update_conversations(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    user_id: uuid.UUID,
):

    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.is_deleted == False,
        Conversation.user_id == user_id,
    )

    conversation = (await db.scalars(stmt)).one_or_none()

    if conversation is None:
        raise ValueError("Conversation not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(conversation, field, value)

    await db.commit()
    await db.refresh(conversation)

    return conversation


async def delete_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
):

    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.is_deleted == False,
        Conversation.user_id == user_id,
    )

    conversation = (await db.scalars(stmt)).one_or_none()

    if conversation is None:
        raise ValueError("Conversation not found")

    setattr(conversation, "is_deleted", True)

    await db.execute(
        update(Message)
        .where(Message.conversation_id == conversation_id)
        .values(is_deleted=True)
    )

    await db.commit()
    await db.refresh(conversation)

    return conversation


# Message Services


async def get_messages(db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID):

    stmt = (
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Message.conversation_id == conversation_id, Message.is_deleted == False, Conversation.user_id == user_id, Conversation.is_deleted == False)
        .order_by(Message.created_at)
    )

    messages = (await db.scalars(stmt)).all()

    return messages


async def delete_message(
    db: AsyncSession, message_id: uuid.UUID, conversation_id: uuid.UUID, user_id: uuid.UUID
):

    stmt = select(Message).join(Conversation, Conversation.id == Message.conversation_id).where(
        Message.conversation_id == conversation_id,
        Message.id == message_id,
        Message.is_deleted == False,
        Conversation.user_id == user_id,
        Conversation.is_deleted == False,
    )

    message = (await db.scalars(stmt)).one_or_none()

    if message is None:
        raise ValueError("Message not found")

    setattr(message, "is_deleted", True)

    await db.commit()
    await db.refresh(message)

    return message


async def create_message(
    db: AsyncSession, conversation_id: uuid.UUID, data: MessageCreate, user_id: uuid.UUID
):
    stmt = select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id ,Conversation.is_deleted == False)

    conversation = (await db.scalars(stmt)).one_or_none()

    if conversation is None:
        raise ValueError("Conversation not found")

    message = Message(
        content=data.content, sender=data.sender, conversation_id=conversation_id
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    await store_message(message, user_id)

    return message
