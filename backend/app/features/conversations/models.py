import enum
import uuid
from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Text, func, ForeignKey, Enum
from datetime import datetime


class SenderEnum(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    slug: Mapped[str]
    title: Mapped[str | None]
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column("isDeleted", default=False)
    created_at: Mapped[datetime] = mapped_column("createdAt", server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", foreign_keys="[Message.conversation_id]"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content: Mapped[str]
    sender: Mapped[SenderEnum] = mapped_column(
        Enum(SenderEnum),
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id")
    )
    is_deleted: Mapped[bool] = mapped_column("isDeleted", default=False)
    created_at: Mapped[datetime] = mapped_column("createdAt", server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages", foreign_keys="[Message.conversation_id]"
    )
