# Document
# ├── id
# ├── user_id
# ├── conversation_id
# ├── filename
# ├── mime_type
# ├── file_size
# ├── s3_key
# ├── processing_status
# ├── error_message
# ├── is_deleted
# ├── created_at
# └── updated_at

import enum
import uuid
from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ARRAY, func, ForeignKey, Enum, String, Integer, Text
from datetime import datetime


class ProcessingStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id")
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    mime_type: Mapped[str] = mapped_column("mimeType", String(255), nullable=False)

    file_size: Mapped[int] = mapped_column("fileSize", Integer, nullable=False)

    s3_key: Mapped[str] = mapped_column(
        "s3Key", String(255), nullable=False, unique=True
    )

    processing_status: Mapped[ProcessingStatusEnum] = mapped_column(
        Enum(ProcessingStatusEnum), nullable=False, default=ProcessingStatusEnum.pending
    )

    error_message: Mapped[str | None] = mapped_column("errorMessage", Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column("isDeleted", default=False)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    topics: Mapped[list[str] | None] = mapped_column("topics", ARRAY(Text), nullable=True)

    summary_status: Mapped[ProcessingStatusEnum] = mapped_column(
        "summaryStatus",
        Enum(ProcessingStatusEnum),
        nullable=False,
        default=ProcessingStatusEnum.pending,
    )

    summary_generated_at: Mapped[datetime | None] = mapped_column(
        "summaryGeneratedAt", nullable=True
    )

    created_at: Mapped[datetime] = mapped_column("createdAt", server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="documents")
    conversation: Mapped["Conversation"] = relationship(back_populates="documents")
