import uuid
from app.core.database import Base
from sqlalchemy import String
from sqlalchemy import func
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    display_name: Mapped[str] = mapped_column("displayName", String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        "email", String(255), nullable=False, unique=True
    )
    hashed_password: Mapped[str] = mapped_column(
        "hashedPassword", String(255), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column("isDeleted", default=False)
    created_at: Mapped[datetime] = mapped_column("createdAt", server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", server_default=func.now(), onupdate=func.now()
    )

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")

    documents: Mapped[list["Document"]] = relationship(back_populates="user")
