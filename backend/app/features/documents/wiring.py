import asyncio
from typing import Callable
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import session_factory
from app.core.dependencies import get_db
from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.wiring import get_conversation_service
from app.features.documents.application.document_processing_service import (
    DocumentProcessingService,
)
from app.features.documents.application.document_service import (
    DocumentService,
)
from app.features.documents.application.interfaces.conversation_operations import (
    ConversationOperations,
)
from app.features.documents.application.interfaces.document_knowledge_pipeline import (
    DocumentKnowledgePipeline,
)
from app.features.documents.application.interfaces.object_storage import (
    ObjectStorage,
)
from app.features.documents.application.interfaces.unit_of_work import (
    DocumentUnitOfWork,
)
from app.features.documents.infrastructure.integrations.conversation_adapter import (
    ConversationAdapter,
)
from app.features.documents.infrastructure.integrations.document_knowledge_pipeline_adapter import (
    DocumentKnowledgePipelineAdapter,
)
from app.features.documents.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyDocumentUnitOfWork,
)
from app.features.documents.infrastructure.storage.s3_storage_adapter import (
    S3StorageAdapter,
)

# Process-scoped concurrency semaphore shared across all DocumentProcessingService calls
_processing_semaphore: asyncio.Semaphore | None = None


def get_processing_semaphore() -> asyncio.Semaphore:
    global _processing_semaphore
    if _processing_semaphore is None:
        concurrency_limit = getattr(
            settings, "MAX_CONCURRENT_DOCUMENT_PROCESSING", 3
        )
        _processing_semaphore = asyncio.Semaphore(concurrency_limit)
    return _processing_semaphore


def get_object_storage() -> ObjectStorage:
    return S3StorageAdapter(
        bucket_name=settings.AWS_S3_BUCKET_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def get_document_uow(
    session: AsyncSession = Depends(get_db),
) -> DocumentUnitOfWork:
    return SQLAlchemyDocumentUnitOfWork(session)


def get_processing_uow_factory() -> Callable[[], DocumentUnitOfWork]:
    def factory() -> DocumentUnitOfWork:
        session = session_factory()
        return SQLAlchemyDocumentUnitOfWork(session, manage_session=True)

    return factory


def get_conversation_operations(
    conv_service: ConversationService = Depends(get_conversation_service),
) -> ConversationOperations:
    return ConversationAdapter(conv_service)


def get_document_knowledge_pipeline() -> DocumentKnowledgePipeline:
    return DocumentKnowledgePipelineAdapter()


def get_document_service(
    uow: DocumentUnitOfWork = Depends(get_document_uow),
    storage: ObjectStorage = Depends(get_object_storage),
    conversation_ops: ConversationOperations = Depends(
        get_conversation_operations
    ),
    knowledge_pipeline: DocumentKnowledgePipeline = Depends(
        get_document_knowledge_pipeline
    ),
) -> DocumentService:
    return DocumentService(
        uow=uow,
        storage=storage,
        conversation_ops=conversation_ops,
        knowledge_pipeline=knowledge_pipeline,
    )


def get_document_processing_service(
    uow_factory: Callable[[], DocumentUnitOfWork] = Depends(
        get_processing_uow_factory
    ),
    storage: ObjectStorage = Depends(get_object_storage),
    knowledge_pipeline: DocumentKnowledgePipeline = Depends(
        get_document_knowledge_pipeline
    ),
    semaphore: asyncio.Semaphore = Depends(get_processing_semaphore),
) -> DocumentProcessingService:
    return DocumentProcessingService(
        uow_factory=uow_factory,
        storage=storage,
        knowledge_pipeline=knowledge_pipeline,
        semaphore=semaphore,
    )
