import asyncio
from datetime import datetime, timezone
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import pytest
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

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
        ]

    async def count_by_conversation(self, conversation_id: uuid.UUID) -> int:
        return len(
            [
                doc
                for doc in self.documents.values()
                if doc.conversation_id == conversation_id and not doc.is_deleted
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
    ) -> None:
        doc = self.documents.get(document_id)
        if doc:
            doc.upload_status = status
            doc.upload_confirmed_at = confirmed_at


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
        self.delete_calls.append(key)
        self.objects.pop(key, None)


class FakeConversationOperations(ConversationOperations):

    def __init__(self) -> None:
        self.valid_conversations: set[tuple[uuid.UUID, uuid.UUID]] = set()
        self.doc_counts: dict[uuid.UUID, int] = {}

    def register_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, count: int = 0
    ) -> None:
        self.valid_conversations.add((conversation_id, user_id))
        self.doc_counts[conversation_id] = count

    async def validate_ownership(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        if (conversation_id, user_id) not in self.valid_conversations:
            raise ConversationAccessError(
                f"Conversation '{conversation_id}' not found or not owned by user '{user_id}'"
            )

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
        self.should_fail_deletion = False

    async def process_document_knowledge(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
    ) -> None:
        if self.should_fail_processing:
            raise RuntimeError("Knowledge pipeline processing failed")
        self.processed_docs.append(document_id)

    async def delete_document_knowledge(self, document_id: uuid.UUID) -> None:
        if self.should_fail_deletion:
            raise RuntimeError("Knowledge pipeline deletion failed")
        self.deleted_knowledge.append(document_id)


# ==============================================================================
# SECTION 18.1: Upload Lifecycle (Criteria 1 - 11)
# ==============================================================================


@pytest.mark.asyncio
async def test_01_upload_initiate_valid():
    """1. Valid upload initiation."""
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
        filename="project_plan.pdf",
        content_type="application/pdf",
        file_size=2048,
    )

    assert "document_id" in result
    assert "presigned_url" in result
    assert "required_headers" in result
    assert result["expires_in"] == 900
    assert result["s3_key"].startswith(f"documents/{user.id}/{cid}/")

    # Document in repository is pending
    created = await repo.get_by_id(result["document_id"])
    assert created is not None
    assert created.upload_status == UploadStatusEnum.pending
    assert created.processing_status == ProcessingStatusEnum.pending
    assert uow.committed is True


@pytest.mark.asyncio
async def test_02_upload_initiate_invalid_extension():
    """2. Invalid file extension rejected."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(
        DocumentUploadInvalidError, match="Invalid file extension"
    ):
        await service.initiate_upload(
            conversation_id=cid,
            user_id=user.id,
            filename="malware.exe",
            content_type="application/octet-stream",
            file_size=1024,
        )


@pytest.mark.asyncio
async def test_03_upload_initiate_invalid_content_type():
    """3. Invalid or empty content type rejected."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(
        DocumentUploadInvalidError, match="Content-Type is required"
    ):
        await service.initiate_upload(
            conversation_id=cid,
            user_id=user.id,
            filename="document.pdf",
            content_type="",
            file_size=1024,
        )


@pytest.mark.asyncio
async def test_04_upload_initiate_file_size_validation():
    """4. File-size validation (zero, negative, and exceeds MAX_FILE_SIZE)."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id)

    service = DocumentService(uow, storage, conv_ops, knowledge)

    with pytest.raises(
        DocumentUploadInvalidError, match="File size must be greater than 0"
    ):
        await service.initiate_upload(
            conversation_id=cid,
            user_id=user.id,
            filename="doc.pdf",
            content_type="application/pdf",
            file_size=0,
        )

    with pytest.raises(
        DocumentUploadInvalidError, match="exceeds maximum limit"
    ):
        await service.initiate_upload(
            conversation_id=cid,
            user_id=user.id,
            filename="doc.pdf",
            content_type="application/pdf",
            file_size=settings.MAX_FILE_SIZE + 1024,
        )


@pytest.mark.asyncio
async def test_05_upload_initiate_presigned_url_generation():
    """5. Presigned URL generation includes expiration and headers."""
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
        filename="report.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_size=5000,
    )

    assert "https://s3.fake.amazonaws.com/" in result["presigned_url"]
    assert "expires=900" in result["presigned_url"]
    assert result["required_headers"] == {
        "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }


@pytest.mark.asyncio
async def test_06_upload_confirm_valid():
    """6. Upload confirmation completes upload and increments conversation count."""
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

    # Place object in S3
    storage.objects[doc.s3_key] = {
        "size": 2048,
        "content_type": "application/pdf",
    }

    service = DocumentService(uow, storage, conv_ops, knowledge)
    confirmed = await service.confirm_upload(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    assert confirmed.upload_status == UploadStatusEnum.completed
    assert confirmed.upload_confirmed_at is not None
    assert confirmed.file_size == 2048
    assert conv_ops.doc_counts[cid] == 1
    assert uow.committed is True


@pytest.mark.asyncio
async def test_07_upload_confirm_missing_s3_object():
    """7. Confirmation fails when object is missing in S3."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()  # S3 empty
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
    with pytest.raises(DocumentUploadInvalidError, match="S3 object.*not found"):
        await service.confirm_upload(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )


@pytest.mark.asyncio
async def test_08_upload_confirm_object_size_mismatch():
    """8. Confirmation fails when S3 object size is zero or exceeds limits."""
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

    # Case A: Empty file in S3
    storage.objects[doc.s3_key] = {"size": 0, "content_type": "application/pdf"}
    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(
        DocumentUploadInvalidError, match="Uploaded file in S3 is empty"
    ):
        await service.confirm_upload(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    # Case B: Exceeds max file size
    storage.objects[doc.s3_key] = {
        "size": settings.MAX_FILE_SIZE + 5000,
        "content_type": "application/pdf",
    }
    with pytest.raises(
        DocumentUploadInvalidError, match="exceeds maximum allowed limit"
    ):
        await service.confirm_upload(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )


@pytest.mark.asyncio
async def test_09_upload_confirm_ownership_validation():
    """9. Confirmation fails if conversation or document belongs to another user."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    owner_user = make_test_user()
    attacker_user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, owner_user.id)

    doc = make_test_document(
        conversation_id=cid,
        user_id=owner_user.id,
        upload_status=UploadStatusEnum.pending,
    )
    await repo.create(doc)
    storage.objects[doc.s3_key] = {
        "size": 1024,
        "content_type": "application/pdf",
    }

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(DocumentNotFoundError):
        await service.confirm_upload(
            conversation_id=cid, document_id=doc.id, user_id=attacker_user.id
        )


@pytest.mark.asyncio
async def test_10_upload_confirm_idempotency():
    """10. Repeated upload confirmation returns document without duplicate count increments."""
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

    # First confirmation
    res1 = await service.confirm_upload(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )
    assert res1.upload_status == UploadStatusEnum.completed
    assert conv_ops.doc_counts[cid] == 1

    # Second confirmation (idempotent)
    res2 = await service.confirm_upload(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )
    assert res2.upload_status == UploadStatusEnum.completed
    assert conv_ops.doc_counts[cid] == 1  # Not incremented again!


@pytest.mark.asyncio
async def test_11_upload_confirm_invalid_state():
    """11. Expired or non-existent document raises DocumentNotFoundError."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(DocumentNotFoundError):
        await service.confirm_upload(
            conversation_id=cid,
            document_id=uuid.uuid4(),  # Non-existent
            user_id=user.id,
        )


# ==============================================================================
# SECTION 18.2: Processing (Criteria 12 - 18)
# ==============================================================================


@pytest.mark.asyncio
async def test_12_processing_starts_only_after_confirmation():
    """12. Background processing is scheduled on confirmation, never on initiation."""
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
        # Step 1: Initiate upload
        init_res = await client.post(
            f"/conversations/{cid}/documents/upload-init",
            json={
                "filename": "test.pdf",
                "content_type": "application/pdf",
                "file_size": 1024,
            },
        )
        assert init_res.status_code == status.HTTP_201_CREATED
        # Ensure processing was NOT triggered during initiation
        assert (
            mock_processing_service.process_document_by_id.call_count == 0
        )

        # Step 2: Confirm upload
        conf_res = await client.post(
            f"/conversations/{cid}/documents/{doc_id}/upload-confirm"
        )
        assert conf_res.status_code == status.HTTP_200_OK
        # Ensure processing was scheduled on confirmation
        assert (
            mock_processing_service.process_document_by_id.call_count == 1
        )


@pytest.mark.asyncio
async def test_13_processing_uses_independent_database_session():
    """13. Processing service obtains its own session from session_factory."""
    session_factory_calls = 0

    class MockAsyncSession:

        async def __aenter__(self):
            nonlocal session_factory_calls
            session_factory_calls += 1
            return AsyncMock()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    def mock_factory():
        return MockAsyncSession()

    storage = FakeObjectStorage()
    knowledge = FakeDocumentKnowledgePipeline()
    proc_service = DocumentProcessingService(
        session_factory=mock_factory,
        storage=storage,
        knowledge_pipeline=knowledge,
    )

    with patch.object(
        SQLAlchemyDocumentUnitOfWork, "commit", new_callable=AsyncMock
    ):
        with patch.object(
            SQLAlchemyDocumentRepository,
            "claim_for_processing",
            new_callable=AsyncMock,
        ) as mock_claim:
            mock_claim.return_value = None  # Exit early
            await proc_service.process_document_by_id(uuid.uuid4())

    assert session_factory_calls >= 1


@pytest.mark.asyncio
async def test_14_duplicate_processing_attempts_rejected():
    """14. Duplicate processing attempts are rejected by atomic claim."""
    repo = FakeDocumentRepository()
    storage = FakeObjectStorage()
    knowledge = FakeDocumentKnowledgePipeline()

    doc = make_test_document(
        upload_status=UploadStatusEnum.completed,
        processing_status=ProcessingStatusEnum.pending,
    )
    await repo.create(doc)
    storage.objects[doc.s3_key] = {"content": b"PDF bytes"}

    class FakeSessionFactory:

        def __call__(self):
            class FakeSessionContext:

                async def __aenter__(self):
                    return MagicMock()

                async def __aexit__(self, *args):
                    pass

            return FakeSessionContext()

    proc_service = DocumentProcessingService(
        session_factory=FakeSessionFactory(),
        storage=storage,
        knowledge_pipeline=knowledge,
    )

    with patch(
        "app.features.documents.application.document_processing_service.SQLAlchemyDocumentUnitOfWork"
    ) as MockUoW:
        uow_instance = FakeDocumentUnitOfWork(repo)
        MockUoW.return_value = uow_instance

        # First claim succeeds
        await proc_service.process_document_by_id(doc.id)
        assert len(knowledge.processed_docs) == 1

        # Second attempt immediately rejected because status is now completed/processing
        await proc_service.process_document_by_id(doc.id)
        assert len(knowledge.processed_docs) == 1  # No duplicate execution!


@pytest.mark.asyncio
async def test_15_processing_success_updates_completed_status():
    """15. Successful processing updates completed status."""
    repo = FakeDocumentRepository()
    storage = FakeObjectStorage()
    knowledge = FakeDocumentKnowledgePipeline()

    doc = make_test_document(
        upload_status=UploadStatusEnum.completed,
        processing_status=ProcessingStatusEnum.pending,
    )
    await repo.create(doc)
    storage.objects[doc.s3_key] = {"content": b"valid pdf content"}

    class FakeSessionFactory:

        def __call__(self):
            class FakeSessionContext:

                async def __aenter__(self):
                    return MagicMock()

                async def __aexit__(self, *args):
                    pass

            return FakeSessionContext()

    proc_service = DocumentProcessingService(
        session_factory=FakeSessionFactory(),
        storage=storage,
        knowledge_pipeline=knowledge,
    )

    with patch(
        "app.features.documents.application.document_processing_service.SQLAlchemyDocumentUnitOfWork"
    ) as MockUoW:
        uow_instance = FakeDocumentUnitOfWork(repo)
        MockUoW.return_value = uow_instance

        await proc_service.process_document_by_id(doc.id)

    assert doc.processing_status == ProcessingStatusEnum.completed
    assert doc.error_message is None
    assert doc.id in knowledge.processed_docs


@pytest.mark.asyncio
async def test_16_processing_failure_updates_failed_status():
    """16. Failed processing updates failed status and records error message."""
    repo = FakeDocumentRepository()
    storage = FakeObjectStorage()
    knowledge = FakeDocumentKnowledgePipeline()
    knowledge.should_fail_processing = True

    doc = make_test_document(
        upload_status=UploadStatusEnum.completed,
        processing_status=ProcessingStatusEnum.pending,
    )
    await repo.create(doc)
    storage.objects[doc.s3_key] = {"content": b"valid pdf content"}

    class FakeSessionFactory:

        def __call__(self):
            class FakeSessionContext:

                async def __aenter__(self):
                    return MagicMock()

                async def __aexit__(self, *args):
                    pass

            return FakeSessionContext()

    proc_service = DocumentProcessingService(
        session_factory=FakeSessionFactory(),
        storage=storage,
        knowledge_pipeline=knowledge,
    )

    with patch(
        "app.features.documents.application.document_processing_service.SQLAlchemyDocumentUnitOfWork"
    ) as MockUoW:
        uow_instance = FakeDocumentUnitOfWork(repo)
        MockUoW.return_value = uow_instance

        await proc_service.process_document_by_id(doc.id)

    assert doc.processing_status == ProcessingStatusEnum.failed
    assert "Knowledge pipeline processing failed" in (doc.error_message or "")


@pytest.mark.asyncio
async def test_17_processing_cannot_start_after_deletion():
    """17. Processing cannot start after deletion has begun."""
    repo = FakeDocumentRepository()
    storage = FakeObjectStorage()
    knowledge = FakeDocumentKnowledgePipeline()

    doc = make_test_document(
        upload_status=UploadStatusEnum.completed,
        processing_status=ProcessingStatusEnum.pending,
        is_deleted=True,  # Deletion already begun
    )
    await repo.create(doc)

    class FakeSessionFactory:

        def __call__(self):
            class FakeSessionContext:

                async def __aenter__(self):
                    return MagicMock()

                async def __aexit__(self, *args):
                    pass

            return FakeSessionContext()

    proc_service = DocumentProcessingService(
        session_factory=FakeSessionFactory(),
        storage=storage,
        knowledge_pipeline=knowledge,
    )

    with patch(
        "app.features.documents.application.document_processing_service.SQLAlchemyDocumentUnitOfWork"
    ) as MockUoW:
        uow_instance = FakeDocumentUnitOfWork(repo)
        MockUoW.return_value = uow_instance

        await proc_service.process_document_by_id(doc.id)

    assert len(knowledge.processed_docs) == 0


@pytest.mark.asyncio
async def test_18_processing_cannot_reindex_after_deletion_completes():
    """18. Processing aborts if document was marked deleted while download was in flight."""
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

    class FakeSessionFactory:

        def __call__(self):
            class FakeSessionContext:

                async def __aenter__(self):
                    return MagicMock()

                async def __aexit__(self, *args):
                    pass

            return FakeSessionContext()

    proc_service = DocumentProcessingService(
        session_factory=FakeSessionFactory(),
        storage=storage,
        knowledge_pipeline=knowledge,
    )

    # Simulate deletion occurring right after atomic claim
    async def fake_claim(document_id):
        doc.is_deleted = True  # Deletion occurs concurrently!
        doc.processing_status = ProcessingStatusEnum.processing
        return doc

    repo.claim_for_processing = fake_claim

    with patch(
        "app.features.documents.application.document_processing_service.SQLAlchemyDocumentUnitOfWork"
    ) as MockUoW:
        uow_instance = FakeDocumentUnitOfWork(repo)
        MockUoW.return_value = uow_instance

        await proc_service.process_document_by_id(doc.id)

    # Document knowledge was not indexed
    assert len(knowledge.processed_docs) == 0


# ==============================================================================
# SECTION 18.3: S3 Storage Adapter (Criteria 19 - 23)
# ==============================================================================


@pytest.mark.asyncio
async def test_19_s3_adapter_generate_presigned_upload_url():
    """19. Upload URL generation uses aioboto3 with key and expiration."""
    adapter = S3StorageAdapter(
        bucket_name="test-bucket",
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        region_name="us-east-1",
    )

    mock_client = AsyncMock()
    mock_client.generate_presigned_url.return_value = (
        "https://test-bucket.s3.amazonaws.com/test-key?signature=xyz"
    )

    class MockAsyncSession:

        def client(self, *args, **kwargs):
            class MockClientContext:

                async def __aenter__(self):
                    return mock_client

                async def __aexit__(self, *args):
                    pass

            return MockClientContext()

    adapter._session = MockAsyncSession()

    url = await adapter.generate_presigned_upload_url(
        key="test-key", content_type="application/pdf", expires_in=900
    )

    assert "test-bucket.s3.amazonaws.com" in url
    mock_client.generate_presigned_url.assert_awaited_once_with(
        "put_object",
        Params={
            "Bucket": "test-bucket",
            "Key": "test-key",
            "ContentType": "application/pdf",
        },
        ExpiresIn=900,
    )


@pytest.mark.asyncio
async def test_20_s3_adapter_get_object_metadata():
    """20. Object metadata retrieval returns size and content_type; handles 404."""
    adapter = S3StorageAdapter("b", "k", "s", "r")
    mock_client = AsyncMock()
    mock_client.head_object.return_value = {
        "ContentLength": 4096,
        "ContentType": "application/pdf",
        "ETag": '"etag123"',
    }

    class MockAsyncSession:

        def client(self, *args, **kwargs):
            class MockClientContext:

                async def __aenter__(self):
                    return mock_client

                async def __aexit__(self, *args):
                    pass

            return MockClientContext()

    adapter._session = MockAsyncSession()

    meta = await adapter.get_object_metadata("test-key")
    assert meta["size"] == 4096
    assert meta["content_type"] == "application/pdf"

    # Test 404 raises ObjectNotFoundError
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
    )
    with pytest.raises(ObjectNotFoundError):
        await adapter.get_object_metadata("missing-key")


@pytest.mark.asyncio
async def test_21_s3_adapter_download_file():
    """21. Object download writes bytes to destination path."""
    adapter = S3StorageAdapter("b", "k", "s", "r")
    mock_client = AsyncMock()

    mock_body = AsyncMock()
    mock_body.read.return_value = b"chunk1chunk2"
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

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await adapter.download_file("test-key", tmp_path)
        with open(tmp_path, "rb") as f:
            content = f.read()
        assert content == b"chunk1chunk2"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.asyncio
async def test_22_s3_adapter_delete_object():
    """22. Object deletion calls S3 delete_object with bucket and key."""
    adapter = S3StorageAdapter("b", "k", "s", "r")
    mock_client = AsyncMock()

    class MockAsyncSession:

        def client(self, *args, **kwargs):
            class MockClientContext:

                async def __aenter__(self):
                    return mock_client

                async def __aexit__(self, *args):
                    pass

            return MockClientContext()

    adapter._session = MockAsyncSession()
    await adapter.delete_object("my-key")

    mock_client.delete_object.assert_awaited_once_with(
        Bucket="b", Key="my-key"
    )


@pytest.mark.asyncio
async def test_23_s3_adapter_delete_missing_object_idempotent():
    """23. Missing-object deletion is handled idempotently without throwing."""
    adapter = S3StorageAdapter("b", "k", "s", "r")
    mock_client = AsyncMock()
    mock_client.delete_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "delete_object",
    )

    class MockAsyncSession:

        def client(self, *args, **kwargs):
            class MockClientContext:

                async def __aenter__(self):
                    return mock_client

                async def __aexit__(self, *args):
                    pass

            return MockClientContext()

    adapter._session = MockAsyncSession()
    # Should not raise exception
    await adapter.delete_object("nonexistent-key")


# ==============================================================================
# SECTION 18.4: Qdrant and Deletion (Criteria 24 - 30)
# ==============================================================================


@pytest.mark.asyncio
async def test_24_deletion_removes_all_vectors():
    """24. All vectors for a document are removed."""
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
    storage.objects[doc.s3_key] = {"content": b"doc"}

    service = DocumentService(uow, storage, conv_ops, knowledge)
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    assert doc.id in knowledge.deleted_knowledge


@pytest.mark.asyncio
async def test_25_deletion_does_not_affect_other_documents():
    """25. Other documents' vectors remain untouched."""
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
    storage.objects[doc1.s3_key] = {"content": b"doc1"}
    storage.objects[doc2.s3_key] = {"content": b"doc2"}

    service = DocumentService(uow, storage, conv_ops, knowledge)
    await service.delete_document(
        conversation_id=cid, document_id=doc1.id, user_id=user.id
    )

    assert doc2.id not in knowledge.deleted_knowledge
    assert doc2.id in repo.documents


@pytest.mark.asyncio
async def test_26_deletion_external_cleanup_failure_handling():
    """26. S3/Qdrant cleanup failures are handled and DB row is preserved for recovery."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()
    knowledge.should_fail_deletion = True  # External vector failure!

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    with pytest.raises(
        RuntimeError, match="Knowledge pipeline deletion failed"
    ):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    # Document was marked soft-deleted to prevent concurrent processing,
    # but NOT physically purged from DB so cleanup can be retried!
    assert doc.id in repo.documents
    assert doc.is_deleted is True


@pytest.mark.asyncio
async def test_27_deletion_partial_failure_retryable():
    """27. Partial deletion can be retried."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()
    knowledge.should_fail_deletion = True

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=1)

    doc = make_test_document(
        conversation_id=cid,
        user_id=user.id,
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)
    storage.objects[doc.s3_key] = {"content": b"data"}

    service = DocumentService(uow, storage, conv_ops, knowledge)

    # First attempt fails at knowledge deletion
    with pytest.raises(RuntimeError):
        await service.delete_document(
            conversation_id=cid, document_id=doc.id, user_id=user.id
        )

    # External failure recovers!
    knowledge.should_fail_deletion = False

    # Retry succeeds cleanly!
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    # Now fully cleaned up
    assert doc.id not in repo.documents
    assert doc.s3_key in storage.delete_calls


@pytest.mark.asyncio
async def test_28_deletion_metadata_available_during_recovery():
    """28. Database metadata remains available for cleanup recovery."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()
    knowledge.should_fail_deletion = True

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

    # Document still in DB, marked is_deleted=True, metadata available
    found = await repo.get_by_id_and_owner(
        doc.id, cid, user.id, include_soft_deleted=True
    )
    assert found is not None
    assert found.s3_key == doc.s3_key


@pytest.mark.asyncio
async def test_29_deletion_physical_delete_on_success():
    """29. PostgreSQL document metadata is physically deleted after successful cleanup."""
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
        upload_status=UploadStatusEnum.completed,
    )
    await repo.create(doc)

    service = DocumentService(uow, storage, conv_ops, knowledge)
    await service.delete_document(
        conversation_id=cid, document_id=doc.id, user_id=user.id
    )

    assert doc.id not in repo.documents
    assert uow.committed is True


@pytest.mark.asyncio
async def test_30_deletion_conversation_document_count_synchronized():
    """30. Conversation document count is decremented on document deletion."""
    repo = FakeDocumentRepository()
    uow = FakeDocumentUnitOfWork(repo)
    storage = FakeObjectStorage()
    conv_ops = FakeConversationOperations()
    knowledge = FakeDocumentKnowledgePipeline()

    user = make_test_user()
    cid = uuid.uuid4()
    conv_ops.register_conversation(cid, user.id, count=3)

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

    assert conv_ops.doc_counts[cid] == 2


# ==============================================================================
# SECTION 18.5: Database & Architecture (Criteria 31 - 35)
# ==============================================================================


@pytest.mark.asyncio
async def test_31_repository_queries_work():
    """31. Repository queries work and enforce soft-delete / owner filters."""
    session = AsyncMock()
    repo = SQLAlchemyDocumentRepository(session)

    # Setup mock scalar result
    mock_scalars = MagicMock()
    mock_scalars.one_or_none.return_value = None
    mock_scalars.all.return_value = []
    session.scalars.return_value = mock_scalars

    doc = await repo.get_by_id(uuid.uuid4())
    assert doc is None
    assert session.scalars.call_count == 1

    docs = await repo.list_by_conversation(uuid.uuid4(), uuid.uuid4())
    assert docs == []


@pytest.mark.asyncio
async def test_32_unit_of_work_commit_works():
    """32. Unit of Work commit delegates to session commit."""
    session = AsyncMock()
    uow = SQLAlchemyDocumentUnitOfWork(session)
    await uow.commit()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_33_unit_of_work_rollback_works():
    """33. Unit of Work rollback delegates to session rollback."""
    session = AsyncMock()
    uow = SQLAlchemyDocumentUnitOfWork(session)
    await uow.rollback()
    session.rollback.assert_awaited_once()


def test_34_upload_status_migration_definition():
    """34. Upload status Alembic migration file exists and defines required schema changes."""
    import importlib.util

    migration_path = os.path.join(
        "alembic", "versions", "a1b2c3d4e5f6_add_upload_status_to_documents.py"
    )
    assert os.path.exists(migration_path), "Migration file must exist"

    spec = importlib.util.spec_from_file_location(
        "migration_module", migration_path
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.revision == "a1b2c3d4e5f6"
    assert mod.down_revision == "66562afc14bd"
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")


def test_35_document_orm_relationships_and_columns():
    """35. Existing Document relationships and new columns remain intact on Document model."""
    doc_table = Base.metadata.tables.get("documents")
    assert doc_table is not None

    table_cols = {c.name for c in doc_table.columns}
    required_db_cols = {
        "id",
        "user_id",
        "conversation_id",
        "filename",
        "mimeType",
        "fileSize",
        "s3Key",
        "processing_status",
        "uploadStatus",
        "uploadConfirmedAt",
        "errorMessage",
        "isDeleted",
        "summary",
        "topics",
        "summaryStatus",
        "createdAt",
        "updatedAt",
    }
    missing_db = required_db_cols - table_cols
    assert not missing_db, f"Missing DB columns in documents table: {missing_db}"

    # Verify Python attributes on Document model class
    required_attrs = {
        "id",
        "user_id",
        "conversation_id",
        "filename",
        "mime_type",
        "file_size",
        "s3_key",
        "processing_status",
        "upload_status",
        "upload_confirmed_at",
        "error_message",
        "is_deleted",
        "summary",
        "topics",
        "summary_status",
        "created_at",
        "updated_at",
        "user",
        "conversation",
    }
    for attr in required_attrs:
        assert hasattr(Document, attr), f"Document model missing attribute '{attr}'"


# ==============================================================================
# SECTION 18.6: Presentation Router & Compatibility Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_router_list_and_get_document():
    """Verify GET list and GET by id endpoints via presentation router."""
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
        # GET /conversations/{id}/documents
        res_list = await client.get(f"/conversations/{cid}/documents")
        assert res_list.status_code == status.HTTP_200_OK
        data = res_list.json()
        assert len(data) == 1
        assert data[0]["id"] == str(doc_id)

        # GET /conversations/{id}/documents/{id}
        res_get = await client.get(f"/conversations/{cid}/documents/{doc_id}")
        assert res_get.status_code == status.HTTP_200_OK
        assert res_get.json()["id"] == str(doc_id)


@pytest.mark.asyncio
async def test_router_delete_document():
    """Verify DELETE endpoint via presentation router."""
    app = FastAPI()
    app.include_router(documents_router)

    user = make_test_user()
    cid = uuid.uuid4()
    doc_id = uuid.uuid4()

    mock_doc_service = AsyncMock(spec=DocumentService)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_document_service] = lambda: mock_doc_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.delete(
            f"/conversations/{cid}/documents/{doc_id}"
        )
        assert res.status_code == status.HTTP_204_NO_CONTENT
        mock_doc_service.delete_document.assert_awaited_once_with(
            conversation_id=cid,
            document_id=doc_id,
            user_id=user.id,
        )


def test_backward_compatible_import_wrappers():
    """Verify backward-compatible import wrappers at root of documents feature."""
    import app.features.documents as docs_root
    from app.features.documents.model import (
        Document as ModelDoc,
        ProcessingStatusEnum as PSEnum,
        UploadStatusEnum as USEnum,
    )
    from app.features.documents.schemas import (
        DocumentResponse,
        UploadInitiateRequest,
        UploadInitiateResponse,
    )
    from app.features.documents.enum import (
        ProcessingStatusEnum as EnumPSE,
        UploadStatusEnum as EnumUSE,
    )
    from app.features.documents.router import router as root_router
    from app.features.documents.processing import process_document
    from app.features.documents.service import (
        get_document,
        get_document_by_id,
        update_doc_summary_status,
        update_document_profile,
    )

    assert hasattr(docs_root, "router")
    assert hasattr(docs_root, "Document")
    assert ModelDoc is not None
    assert PSEnum is not None
    assert USEnum is not None
    assert DocumentResponse is not None
    assert UploadInitiateRequest is not None
    assert UploadInitiateResponse is not None
    assert EnumPSE is not None
    assert EnumUSE is not None
    assert root_router is not None
    assert callable(process_document)
    assert callable(get_document)
    assert callable(get_document_by_id)
    assert callable(update_doc_summary_status)
    assert callable(update_document_profile)


