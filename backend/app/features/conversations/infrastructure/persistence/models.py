import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.features.conversations.application.enums import SenderEnum

if TYPE_CHECKING:
    from app.features.auth.infrastructure.persistence.models import User
    from app.features.documents.model import Document


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    slug: Mapped[str]
    title: Mapped[str | None]
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column("isDeleted", default=False)
    created_at: Mapped[datetime] = mapped_column("createdAt", server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", server_default=func.now(), onupdate=func.now()
    )
    document_count: Mapped[int] = mapped_column("documentCount", default=0)

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")
    user: Mapped["User"] = relationship(back_populates="conversations")
    documents: Mapped[list["Document"]] = relationship(back_populates="conversation")


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

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

