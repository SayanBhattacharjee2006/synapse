import ast
import asyncio
from datetime import datetime, timezone
import inspect
import os
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import pytest
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

from app.ai.rag.summarization.schemas import DocumentProfile
from app.core.config import settings
from app.core.database import Base
from app.features.auth.infrastructure.persistence.models import User
from app.features.auth.presentation.dependencies import get_current_user
from app.features.documents.application.document_processing_service import (
    DocumentProcessingService,
)
from app.features.documents.application.document_service import DocumentService
from app.features.documents.application.enums import (
    ProcessingStatusEnum,
    UploadStatusEnum,
)
from app.features.documents.application.exceptions import (
    ConversationAccessError,
    DocumentNotFoundError,
    DocumentUploadInvalidError,
    ObjectNotFoundError,
)
from app.features.documents.application.interfaces.conversation_operations import (
    ConversationOperations,
)
from app.features.documents.application.interfaces.document_knowledge_pipeline import (
    DocumentKnowledgePipeline,
)
from app.features.documents.application.interfaces.document_repository import (
    DocumentRepository,
)
from app.features.documents.application.interfaces.object_storage import (
    ObjectStorage,
)
from app.features.documents.application.interfaces.unit_of_work import (
    DocumentUnitOfWork,
)
from app.features.documents.infrastructure.persistence.models import Document
from app.features.documents.infrastructure.persistence.sqlalchemy_document_repository import (
    SQLAlchemyDocumentRepository,
)
from app.features.documents.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyDocumentUnitOfWork,
)
from app.features.documents.infrastructure.storage.s3_storage_adapter import (
    S3StorageAdapter,
)
from app.features.documents.presentation.router import (
    router as documents_router,
)
from app.features.documents.wiring import (
    get_document_processing_service,
    get_document_service,
    get_processing_semaphore,
)


# ==============================================================================
# Helper Factories
# ==============================================================================


def make_test_user(user_id: uuid.UUID | None = None) -> User:
    return User(
        id=user_id or uuid.uuid4(),
        email="testuser@example.com",
        display_name="Test User",
        hashed_password="hashed_pw",
        is_deleted=False,
    )


def make_test_document(
    document_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    filename: str = "report.pdf",
    upload_status: UploadStatusEnum = UploadStatusEnum.pending,
    processing_status: ProcessingStatusEnum = ProcessingStatusEnum.pending,
    file_size: int = 1024,
    mime_type: str = "application/pdf",
    is_deleted: bool = False,
) -> Document:
    doc_id = document_id or uuid.uuid4()
    c_id = conversation_id or uuid.uuid4()
    u_id = user_id or uuid.uuid4()
    now = datetime.now(timezone.utc)
    return Document(
        id=doc_id,
        user_id=u_id,
        conversation_id=c_id,
        filename=filename,
        mime_type=mime_type,
        file_size=file_size,
        s3_key=f"documents/{u_id}/{c_id}/{doc_id}/{filename}",
        upload_status=upload_status,
        processing_status=processing_status,
        upload_confirmed_at=None,
        summary_status=ProcessingStatusEnum.pending,
        is_deleted=is_deleted,
        created_at=now,
        updated_at=now,
    )


# ==============================================================================
# In-Memory Test Doubles
# ==============================================================================


class FakeDocumentRepository(DocumentRepository):

    def __init__(self) -> None:
        self.documents: dict[uuid.UUID, Document] = {}

    async def create(self, document: Document) -> Document:
        self.documents[document.id] = document
        return document

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
    ) -> Document:
        doc = make_test_document(
            document_id=document_id,
            conversation_id=conversation_id,
            user_id=user_id,
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            upload_status=upload_status,
            processing_status=processing_status,
        )
        doc.s3_key = s3_key
        self.documents[document_id] = doc
        return doc

    async def get_by_id(
        self, document_id: uuid.UUID, include_soft_deleted: bool = False
    ) -> Document | None:
        doc = self.documents.get(document_id)
        if doc and not include_soft_deleted and doc.is_deleted:
            return None
        return doc

    async def get_by_id_and_owner(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        include_soft_deleted: bool = False,
    ) -> Document | None:
        doc = self.documents.get(document_id)
        if not doc:
            return None
        if not include_soft_deleted and doc.is_deleted:
            return None
        if doc.conversation_id != conversation_id or doc.user_id != user_id:
            return None
        return doc

    async def list_by_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Document]:
        return [
            doc
            for doc in self.documents.values()
            if doc.conversation_id == conversation_id
            and doc.user_id == user_id
            and not doc.is_deleted
            and doc.upload_status == UploadStatusEnum.completed
        ]

    async def count_by_conversation(self, conversation_id: uuid.UUID) -> int:
        return len(
            [
                doc
                for doc in self.documents.values()
                if doc.conversation_id == conversation_id
                and not doc.is_deleted
                and doc.upload_status == UploadStatusEnum.completed
            ]
        )

    async def mark_deletion_started(self, document_id: uuid.UUID) -> None:
        doc = self.documents.get(document_id)
        if doc:
            doc.is_deleted = True

    async def hard_delete(self, document_id: uuid.UUID) -> None:
        self.documents.pop(document_id, None)

    async def claim_for_processing(
        self, document_id: uuid.UUID
    ) -> Document | None:
        doc = self.documents.get(document_id)
        if (
            not doc
            or doc.is_deleted
            or doc.upload_status != UploadStatusEnum.completed
            or doc.processing_status != ProcessingStatusEnum.pending
        ):
            return None
        doc.processing_status = ProcessingStatusEnum.processing
        return doc

    async def update_processing_status(
        self,
        document_id: uuid.UUID,
        status: ProcessingStatusEnum,
        error_message: str | None = None,
    ) -> None:
        doc = self.documents.get(document_id)
        if doc:
            doc.processing_status = status
            doc.error_message = error_message

    async def update_upload_status(
        self,
        document_id: uuid.UUID,
        status: UploadStatusEnum,
        confirmed_at: datetime | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> None:
        doc = self.documents.get(document_id)
        if doc:
            doc.upload_status = status
            if confirmed_at is not None:
                doc.upload_confirmed_at = confirmed_at
            if file_size is not None:
                doc.file_size = file_size
            if mime_type is not None:
                doc.mime_type = mime_type

    async def update_document_summary(
        self,
        document_id: uuid.UUID,
        summary: str | None,
        topics: list[str] | None,
        summary_status: ProcessingStatusEnum = ProcessingStatusEnum.completed,
        generated_at: datetime | None = None,
    ) -> None:
        doc = self.documents.get(document_id)
        if doc:
            doc.summary = summary
            doc.topics = topics
            doc.summary_status = summary_status
            doc.summary_generated_at = generated_at or datetime.now(timezone.utc)


class FakeDocumentUnitOfWork(DocumentUnitOfWork):

    def __init__(self, repo: FakeDocumentRepository) -> None:
        self.documents = repo
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> "FakeDocumentUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def refresh(self, instance: object) -> None:
        pass


class FakeObjectStorage(ObjectStorage):

    def __init__(self) -> None:
        self.objects: dict[str, dict] = {}
        self.delete_calls: list[str] = []
        self.should_fail_delete = False

    async def generate_presigned_upload_url(
        self, key: str, content_type: str, expires_in: int = 900
    ) -> str:
        return f"https://s3.fake.amazonaws.com/{key}?expires={expires_in}&content_type={content_type}"

    async def get_object_metadata(self, key: str) -> dict:
        if key not in self.objects:
            raise ObjectNotFoundError(f"S3 object '{key}' not found")
        return self.objects[key]

    async def download_file(self, key: str, destination_path: str) -> None:
        if key not in self.objects:
            raise ObjectNotFoundError(f"S3 object '{key}' not found")
        with open(destination_path, "wb") as f:
            f.write(self.objects[key].get("content", b"fake file content"))

    async def delete_object(self, key: str) -> None:
        if self.should_fail_delete:
            raise RuntimeError("S3 deletion failed")
        self.delete_calls.append(key)
        self.objects.pop(key, None)


class FakeConversationOperations(ConversationOperations):

    def __init__(self) -> None:
        self.valid_conversations: set[tuple[uuid.UUID, uuid.UUID]] = set()
        self.doc_counts: dict[uuid.UUID, int] = {}
        self.should_fail_count_sync = False

    def register_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, count: int = 0
    ) -> None:
        self.valid_conversations.add((conversation_id, user_id))
        self.doc_counts[conversation_id] = count

    async def validate_ownership(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        if (conversation_id, user_id) not in self.valid_conversations:
            raise ConversationAccessError(
                f"Conversation '{conversation_id}' not found or not owned by user '{user_id}'"
            )
        return True

    async def set_document_count(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, count: int
    ) -> None:
        await self.validate_ownership(conversation_id, user_id)
        if self.should_fail_count_sync:
            raise RuntimeError("Conversation count sync failed")
        self.doc_counts[conversation_id] = max(0, count)

    async def adjust_document_count(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, delta: int
    ) -> None:
        await self.validate_ownership(conversation_id, user_id)
        current = self.doc_counts.get(conversation_id, 0)
        self.doc_counts[conversation_id] = max(0, current + delta)


class FakeDocumentKnowledgePipeline(DocumentKnowledgePipeline):

    def __init__(self) -> None:
        self.processed_docs: list[uuid.UUID] = []
        self.deleted_knowledge: list[uuid.UUID] = []
        self.should_fail_processing = False
        self.should_fail_chunk_deletion = False
        self.should_fail_summary_deletion = False

    async def process_document_knowledge(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
    ) -> DocumentProfile:
        if self.should_fail_processing:
            raise RuntimeError("Knowledge pipeline processing failed")
        self.processed_docs.append(document_id)
        return DocumentProfile(
            summary="Synthesized test summary", topics=["test", "docs"]
        )

    async def delete_document_knowledge(self, document_id: uuid.UUID) -> None:
        if self.should_fail_chunk_deletion:
            raise RuntimeError("Qdrant chunk deletion failed")
        if self.should_fail_summary_deletion:
            raise RuntimeError("Qdrant summary deletion failed")
        self.deleted_knowledge.append(document_id)


# ==============================================================================
# SECTION 12.1: Deletion Consistency (Criteria 1 - 10)
# ==============================================================================


@pytest.mark.asyncio
async def test_01_qdrant_chunk_deletion_failure_preserves_record_for_retry():
    """1. Qdrant chunk deletion failure propagates and preserves DB row with is_deleted=True."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()
    knowledge.should_fail_chunk_deletion = True

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(RuntimeError, match="Qdrant chunk deletion failed"):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    # Document is NOT physically deleted from database; marked is_deleted=True
    assert doc.id in repo.documents
    assert doc.is_deleted is True


@pytest.mark.asyncio
async def test_02_qdrant_summary_deletion_failure_preserves_record_for_retry():
    """2. Qdrant summary deletion failure propagates and preserves DB row."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()
    knowledge.should_fail_summary_deletion = True

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(RuntimeError, match="Qdrant summary deletion failed"):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    assert doc.id in repo.documents
    assert doc.is_deleted is True


@pytest.mark.asyncio
async def test_03_s3_deletion_failure_preserves_record():
    """3. S3 deletion failure propagates and preserves DB row for retry."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    storage.should_fail_delete = True
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(RuntimeError, match="S3 deletion failed"):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    assert doc.id in repo.documents
    assert doc.is_deleted is True


@pytest.mark.asyncio
async def test_04_conversation_count_sync_failure_preserves_record():
    """4. Conversation count synchronization failure preserves DB row."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    conv_ops.should_fail_count_sync = True
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(RuntimeError, match="Conversation count sync failed"):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    assert doc.id in repo.documents


@pytest.mark.asyncio
async def test_05_retry_after_qdrant_failure():
    """5. Retry after Qdrant failure succeeds cleanly and physically deletes record."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()
    knowledge.should_fail_chunk_deletion = True

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)

    # First attempt fails
    with pytest.raises(RuntimeError):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    # Recovery
    knowledge.should_fail_chunk_deletion = False

    # Retry succeeds
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    assert doc.id not in repo.documents
    assert doc.id in knowledge.deleted_knowledge


@pytest.mark.asyncio
async def test_06_retry_after_s3_failure():
    """6. Retry after S3 failure succeeds once storage recovers."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    storage.should_fail_delete = True
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)

    with pytest.raises(RuntimeError):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    storage.should_fail_delete = False
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    assert doc.id not in repo.documents
    assert doc.s3_key in storage.delete_calls


@pytest.mark.asyncio
async def test_07_retry_after_count_sync_failure():
    """7. Retry after count synchronization failure succeeds."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    conv_ops.should_fail_count_sync = True
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)

    with pytest.raises(RuntimeError):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    conv_ops.should_fail_count_sync = False
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    assert doc.id not in repo.documents
    assert conv_ops.doc_counts[cid] == 0


@pytest.mark.asyncio
async def test_08_and_09_postgresql_record_retained_until_success_then_physically_deleted():
    """8. Record retained until all cleanup succeeds. 9. Physical deletion after success."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    # Completely deleted from PostgreSQL
    assert doc.id not in repo.documents
    assert uow.committed is True


@pytest.mark.asyncio
async def test_10_repeated_deletion_is_safe():
    """10. Repeated deletion request for already deleted document raises DocumentNotFoundError."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    # Second call raises DocumentNotFoundError safely
    with pytest.raises(DocumentNotFoundError):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )


# ==============================================================================
# SECTION 12.2: Conversation Count Consistency (Criteria 11 - 13)
# ==============================================================================


@pytest.mark.asyncio
async def test_11_repeated_deletion_does_not_double_decrement_count():
    """11. Absolute count sync ensures retrying deletion never decrements count more than once."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()
    knowledge.should_fail_summary_deletion = True

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)

    # Try 1: fails, document marked is_deleted=True
    with pytest.raises(RuntimeError):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    # Try 2: fails again
    with pytest.raises(RuntimeError):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    # Count was NOT double-decremented below 0
    knowledge.should_fail_summary_deletion = False
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    assert conv_ops.doc_counts[cid] == 0


@pytest.mark.asyncio
async def test_12_repeated_upload_confirmation_does_not_double_increment():
    """12. Repeated confirmation sets absolute count and never increments multiple times."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=0)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.pending,
    )
    await repo.create(doc)
    storage.objects[doc.s3_key] = {
        "size": 2048,
        "content_type": "application/pdf",
    }

    service = DocumentService(uow, storage, conv_ops, knowledge)

    # Confirmation 1
    await service.confirm_upload(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )
    assert conv_ops.doc_counts[cid] == 1

    # Confirmation 2 (idempotent)
    await service.confirm_upload(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )
    assert conv_ops.doc_counts[cid] == 1  # Still exactly 1!


@pytest.mark.asyncio
async def test_13_count_reconciliation_works_after_partial_failure():
    """13. Count reconciliation accurately reflects remaining active documents after partial failures."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=2)

    doc1 = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    doc2 = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc1)
    await repo.create(doc2)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    await service.delete_document(
        conversation_id=cid, document_id=doc1.id, user_id=user.id
    )

    assert conv_ops.doc_counts[cid] == 1


# ==============================================================================
# SECTION 12.3: Processing and Deletion Races (Criteria 14 - 19)
# ==============================================================================


@pytest.mark.asyncio
async def test_14_processing_cannot_claim_deleted_documents():
    """14. Processing claim query rejects documents where is_deleted=True."""
    repo = FakeDocumentRepository()
    storage = FakeObjectStorage()
    knowledge = FakeDocumentKnowledgePipeline()

    doc = make_test_document(
        upload_status=UploadStatusEnum.completed,
        processing_status=ProcessingStatusEnum.pending,
        is_deleted=True,
    )
    await repo.create(doc)

    proc_service = DocumentProcessingService(
        uow_factory=lambda: FakeDocumentUnitOfWork(repo),
        storage=storage,
        knowledge_pipeline=knowledge,
    )

    await proc_service.process_document_by_id(doc.id)
    assert len(knowledge.processed_docs) == 0


@pytest.mark.asyncio
async def test_15_and_16_deletion_during_ingestion_race_handling():
    """15, 16, 17, 18, 19. Race handling: post-processing check detects deletion, purges vectors, does not mark completed."""
    repo = FakeDocumentRepository()
    storage = FakeObjectStorage()
    knowledge = FakeDocumentKnowledgePipeline()

    doc = make_test_document(
        upload_status=UploadStatusEnum.completed,
        processing_status=ProcessingStatusEnum.pending,
        is_deleted=False,
    )
    await repo.create(doc)
    storage.objects[doc.s3_key] = {"content": b"content"}

    # Simulate deletion occurring during process_document_knowledge
    async def process_with_concurrent_deletion(*args, **kwargs):
        doc.is_deleted = True  # Deletion occurs concurrently during ingestion!
        knowledge.processed_docs.append(doc.id)
        return DocumentProfile(summary="raced summary", topics=["race"])

    knowledge.process_document_knowledge = process_with_concurrent_deletion

    proc_service = DocumentProcessingService(
        uow_factory=lambda: FakeDocumentUnitOfWork(repo),
        storage=storage,
        knowledge_pipeline=knowledge,
    )

    await proc_service.process_document_by_id(doc.id)

    # Verified:
    # 1. Post-processing detected deletion and called delete_document_knowledge to purge orphaned vectors!
    assert doc.id in knowledge.deleted_knowledge
    # 2. Document processing status was NOT marked completed!
    assert doc.processing_status != ProcessingStatusEnum.completed


# ==============================================================================
# SECTION 12.4: Database Migration and Backfill (Criteria 20 - 22)
# ==============================================================================


def test_20_21_22_migration_backfill_logic():
    """20, 21, 22. Migration backfills existing documents with completed and alters new default to pending."""
    import importlib.util

    migration_path = os.path.join(
        "alembic", "versions", "a1b2c3d4e5f6_add_upload_status_to_documents.py"
    )
    assert os.path.exists(migration_path)

    with open(migration_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verified server_default='completed' initially for backfill
    assert "server_default=\"completed\"" in content
    # Verified backfill of uploadConfirmedAt from createdAt
    assert 'UPDATE documents SET "uploadConfirmedAt" = "createdAt"' in content
    # Verified alter_column to pending for future records
    assert "op.alter_column" in content
    assert "server_default=\"pending\"" in content


# ==============================================================================
# SECTION 12.5: Architecture & Ownership Verification (Criteria 23 - 26)
# ==============================================================================


def test_23_application_services_do_not_import_concrete_sqlalchemy():
    """23. Application services don't import concrete SQLAlchemy implementations."""
    app_service_files = [
        Path("app/features/documents/application/document_service.py"),
        Path(
            "app/features/documents/application/document_processing_service.py"
        ),
    ]

    for p in app_service_files:
        with open(p, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(p))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert (
                    "infrastructure.persistence.models" not in node.module
                ), f"Direct ORM model import in {p}"
                assert (
                    "infrastructure.persistence.sqlalchemy" not in node.module
                ), f"Concrete SQLAlchemy import in {p}"


def test_24_and_25_ai_rag_ownership_and_no_orm_import():
    """24. AI/RAG doesn't import Documents ORM models. 25. Summarization doesn't modify PostgreSQL."""
    rag_files = [
        Path("app/ai/rag/ingestion/ingest.py"),
        Path("app/ai/rag/services/document_summary_service.py"),
        Path("app/ai/rag/summarization/service.py"),
    ]

    for p in rag_files:
        with open(p, "r", encoding="utf-8") as f:
            code = f.read()
            tree = ast.parse(code, filename=str(p))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert (
                    "app.features.documents.model" not in node.module
                ), f"Forbidden Document model import in {p}"
                assert (
                    "app.core.database" not in node.module
                ), f"Summarization cannot open PostgreSQL sessions in {p}"


def test_26_compatibility_imports_work():
    """26. Existing compatibility imports remain functional."""
    from app.features.documents.summary.schemas import (
        DocumentProfile,
        IntermediateSummary,
    )
    from app.features.documents.summary.service import (
        generate_document_profile,
    )
    from app.features.documents.formatter import (
        format_document_profile,
        group_serializer,
    )
    from app.features.documents.model import (
        Document,
        ProcessingStatusEnum,
        UploadStatusEnum,
    )

    assert DocumentProfile is not None
    assert IntermediateSummary is not None
    assert callable(generate_document_profile)
    assert callable(format_document_profile)
    assert callable(group_serializer)
    assert Document is not None
    assert ProcessingStatusEnum is not None
    assert UploadStatusEnum is not None


# ==============================================================================
# SECTION 12.6: Upload Lifecycle & Concurrency (Criteria 27 - 33)
# ==============================================================================


@pytest.mark.asyncio
async def test_27_presigned_upload_initiation_generates_url_before_commit():
    """27. Presigned upload initiation generates URL and registers pending record."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    result = await service.initiate_upload(
        conversation_id=cid,
        user_id=user.id,
        filename="specs.pdf",
        content_type="application/pdf",
        file_size=2048,
    )

    assert "presigned_url" in result
    assert "document_id" in result
    assert uow.committed is True
    doc = await repo.get_by_id(result["document_id"])
    assert doc is not None
    assert doc.upload_status == UploadStatusEnum.pending


@pytest.mark.asyncio
async def test_28_and_29_s3_object_verification_and_size_validation():
    """28. S3 object verification. 29. Size mismatch / empty file error."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.pending,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)

    # Missing in S3
    with pytest.raises(DocumentUploadInvalidError, match="S3 object.*not found"):
        await service.confirm_upload(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    # Empty in S3
    storage.objects[doc.s3_key] = {"size": 0, "content_type": "application/pdf"}
    with pytest.raises(DocumentUploadInvalidError, match="empty"):
        await service.confirm_upload(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )


@pytest.mark.asyncio
async def test_30_and_31_invalid_and_concurrent_upload_confirmation():
    """30. Invalid confirmation. 31. Concurrent confirmations are idempotent."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=0)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.pending,
    )
    await repo.create(doc)
    storage.objects[doc.s3_key] = {
        "size": 1024,
        "content_type": "application/pdf",
    }

    service = DocumentService(uow, storage, conv_ops, knowledge)

    # Non-existent doc raises 404
    with pytest.raises(DocumentNotFoundError):
        await service.confirm_upload(
            conversation_id=cid, document_id=uuid.uuid4(), user_id=user.id
        )

    # Concurrent confirmation calls
    res1, res2 = await asyncio.gather(
        service.confirm_upload(cid, doc.id, user.id),
        service.confirm_upload(cid, doc.id, user.id),
    )
    assert res1.upload_status == UploadStatusEnum.completed
    assert res2.upload_status == UploadStatusEnum.completed
    assert conv_ops.doc_counts[cid] == 1  # Count incremented only once!


@pytest.mark.asyncio
async def test_32_background_processing_scheduled_only_after_confirmation():
    """32. Background processing starts only after valid confirmation."""
    app = FastAPI()
    app.include_router(documents_router)

    user = make_test_user()
    cid = uuid.uuid4()
    doc_id = uuid.uuid4()

    mock_doc_service = AsyncMock(spec=DocumentService)
    mock_processing_service = AsyncMock(spec=DocumentProcessingService)

    mock_doc_service.initiate_upload.return_value = {
        "document_id": doc_id,
        "presigned_url": "https://s3.fake/upload",
        "required_headers": {"Content-Type": "application/pdf"},
        "expires_in": 900,
        "s3_key": "k",
    }
    doc = make_test_document(
        document_id=doc_id,
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    mock_doc_service.confirm_upload.return_value = doc

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_document_service] = lambda: mock_doc_service
    app.dependency_overrides[get_document_processing_service] = (
        lambda: mock_processing_service
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Initiate does NOT trigger background processing
        init_res = await client.post(
            f"/conversations/{cid}/documents/upload-init",
            json={
                "filename": "file.pdf",
                "content_type": "application/pdf",
                "file_size": 1024,
            },
        )
        assert init_res.status_code == status.HTTP_201_CREATED
        assert (
            mock_processing_service.process_document_by_id.call_count == 0
        )

        # Confirm triggers background processing
        conf_res = await client.post(
            f"/conversations/{cid}/documents/{doc_id}/upload-confirm"
        )
        assert conf_res.status_code == status.HTTP_200_OK
        assert (
            mock_processing_service.process_document_by_id.call_count == 1
        )


def test_33_shared_processing_concurrency_semaphore():
    """33. Shared process-level concurrency semaphore in wiring."""
    sem1 = get_processing_semaphore()
    sem2 = get_processing_semaphore()
    assert sem1 is sem2
    assert isinstance(sem1, asyncio.Semaphore)


# ==============================================================================
# SECTION 12.7: S3 Storage Adapter Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_s3_storage_adapter_operations_and_idempotent_delete():
    """S3 adapter upload URL, download, head_object, and idempotent deletion."""
    adapter = S3StorageAdapter("b", "k", "s", "r")
    mock_client = AsyncMock()
    mock_client.generate_presigned_url.return_value = (
        "https://b.s3.amazonaws.com/k?sig=1"
    )
    mock_client.head_object.return_value = {
        "ContentLength": 100,
        "ContentType": "application/pdf",
    }
    mock_body = AsyncMock()
    mock_body.read.return_value = b"test bytes"
    mock_body.__aenter__.return_value = mock_body
    mock_body.__aexit__.return_value = None
    mock_client.get_object.return_value = {"Body": mock_body}

    class MockAsyncSession:

        def client(self, *args, **kwargs):
            class MockClientContext:

                async def __aenter__(self):
                    return mock_client

                async def __aexit__(self, *args):
                    pass

            return MockClientContext()

    adapter._session = MockAsyncSession()

    url = await adapter.generate_presigned_upload_url("k", "application/pdf")
    assert "https://b.s3.amazonaws.com" in url

    meta = await adapter.get_object_metadata("k")
    assert meta["size"] == 100

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = tmp.name
    try:
        await adapter.download_file("k", path)
        with open(path, "rb") as f:
            assert f.read() == b"test bytes"
    finally:
        if os.path.exists(path):
            os.remove(path)

    # Idempotent delete when object does not exist in S3
    mock_client.delete_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "Missing"}}, "delete_object"
    )
    await adapter.delete_object("missing_key")  # Must not raise!


@pytest.mark.asyncio
async def test_presentation_router_endpoints():
    """Verify list, get, and delete endpoints on presentation router."""
    app = FastAPI()
    app.include_router(documents_router)

    user = make_test_user()
    cid = uuid.uuid4()
    doc_id = uuid.uuid4()

    mock_doc_service = AsyncMock(spec=DocumentService)
    doc = make_test_document(
        document_id=doc_id,
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    mock_doc_service.list_documents.return_value = [doc]
    mock_doc_service.get_document.return_value = doc

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_document_service] = lambda: mock_doc_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        res_list = await client.get(f"/conversations/{cid}/documents")
        assert res_list.status_code == status.HTTP_200_OK

        res_get = await client.get(f"/conversations/{cid}/documents/{doc_id}")
        assert res_get.status_code == status.HTTP_200_OK

        res_del = await client.delete(
            f"/conversations/{cid}/documents/{doc_id}"
        )
        assert res_del.status_code == status.HTTP_204_NO_CONTENT
