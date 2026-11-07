import uuid

from app.features.documents.wiring import (
    get_document_knowledge_pipeline,
    get_document_processing_service,
    get_object_storage,
)


async def process_document(document_id: uuid.UUID) -> None:
    storage = get_object_storage()
    knowledge_pipeline = get_document_knowledge_pipeline()
    service = get_document_processing_service(
        storage=storage,
        knowledge_pipeline=knowledge_pipeline,
    )
    await service.process_document_by_id(document_id)


__all__ = ["process_document"]
