from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from app.features.documents.application.enums import (
    ProcessingStatusEnum,
    UploadStatusEnum,
)

if TYPE_CHECKING:
    from app.features.documents.infrastructure.persistence.models import (
        Document,
    )


class DocumentRepository(ABC):

    @abstractmethod
    async def create(self, document: "Document") -> "Document":
        """Add a document to persistence (without committing)."""
        raise NotImplementedError

    @abstractmethod
    async def create_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        filename: str,
        mime_type: str,
        file_size: int,
        s3_key: str,
        upload_status: UploadStatusEnum = UploadStatusEnum.pending,
        processing_status: ProcessingStatusEnum = ProcessingStatusEnum.pending,
    ) -> "Document":
        """Construct and add a new Document instance to persistence."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self, document_id: uuid.UUID, include_soft_deleted: bool = False
    ) -> "Document | None":
        """Retrieve a document by ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_and_owner(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        include_soft_deleted: bool = False,
    ) -> "Document | None":
        """Retrieve a document by ID with conversation and user ownership checks."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> list["Document"]:
        """List active documents for a conversation owned by user."""
        raise NotImplementedError

    @abstractmethod
    async def count_by_conversation(self, conversation_id: uuid.UUID) -> int:
        """Count active, successfully uploaded documents for a conversation."""
        raise NotImplementedError

    @abstractmethod
    async def claim_for_processing(
        self, document_id: uuid.UUID
    ) -> "Document | None":
        """Atomically claim a document for processing if upload completed, processing pending, and not deleted."""
        raise NotImplementedError

    @abstractmethod
    async def update_processing_status(
        self,
        document_id: uuid.UUID,
        status: ProcessingStatusEnum,
        error_message: str | None = None,
    ) -> None:
        """Update processing status and optional error message."""
        raise NotImplementedError

    @abstractmethod
    async def update_upload_status(
        self,
        document_id: uuid.UUID,
        status: UploadStatusEnum,
        confirmed_at: datetime | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> None:
        """Update upload status and confirmation metadata."""
        raise NotImplementedError

    @abstractmethod
    async def update_document_summary(
        self,
        document_id: uuid.UUID,
        summary: str | None,
        topics: list[str] | None,
        summary_status: ProcessingStatusEnum = ProcessingStatusEnum.completed,
        generated_at: datetime | None = None,
    ) -> None:
        """Update document summary, topics, and summary status."""
        raise NotImplementedError

    @abstractmethod
    async def mark_deletion_started(self, document_id: uuid.UUID) -> None:
        """Mark document as deletion in-progress (soft-delete)."""
        raise NotImplementedError

    @abstractmethod
    async def hard_delete(self, document_id: uuid.UUID) -> None:
        """Permanently remove document record from PostgreSQL."""
        raise NotImplementedError
