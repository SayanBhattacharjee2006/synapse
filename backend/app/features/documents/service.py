from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.document_profile import DocumentProfile
from app.features.documents.application.enums import ProcessingStatusEnum
from app.features.documents.infrastructure.persistence.models import Document


async def update_document_profile(
    doc: Document,
    document_profile: DocumentProfile,
) -> Document:
    doc.summary = document_profile.summary
    doc.topics = document_profile.topics
    return doc


async def update_doc_summary_status(
    doc: Document,
    status: ProcessingStatusEnum,
    generated_time: datetime | None = None,
) -> Document:
    doc.summary_status = status
    if generated_time:
        doc.summary_generated_at = generated_time
    return doc


async def get_document_by_id(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
) -> Document | None:
    from app.features.documents.infrastructure.persistence.sqlalchemy_document_repository import (
        SQLAlchemyDocumentRepository,
    )

    repo = SQLAlchemyDocumentRepository(db)
    return await repo.get_by_id_and_owner(
        document_id, conversation_id, user_id
    )


async def get_document(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[Document]:
    from app.features.documents.infrastructure.persistence.sqlalchemy_document_repository import (
        SQLAlchemyDocumentRepository,
    )

    repo = SQLAlchemyDocumentRepository(db)
    return await repo.list_by_conversation(conversation_id, user_id)


async def delete_document(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    from app.features.documents.wiring import (
        get_conversation_operations,
        get_document_knowledge_pipeline,
        get_document_service,
        get_document_uow,
        get_object_storage,
    )
    from app.features.conversations.application.conversation_service import (
        ConversationService,
    )
    from app.features.conversations.infrastructure.persistence.sqlalchemy_unit_of_work import (
        SQLAlchemyConversationsUnitOfWork,
    )

    uow = get_document_uow(db)
    storage = get_object_storage()
    conv_uow = SQLAlchemyConversationsUnitOfWork(db)
    conv_service = ConversationService(conv_uow)
    conv_ops = get_conversation_operations(conv_service)
    knowledge = get_document_knowledge_pipeline()

    service = get_document_service(uow, storage, conv_ops, knowledge)
    await service.delete_document(conversation_id, document_id, user_id)


__all__ = [
    "update_document_profile",
    "update_doc_summary_status",
    "get_document_by_id",
    "get_document",
    "delete_document",
]
