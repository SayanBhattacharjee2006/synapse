import uuid

from app.ai.rag.document_knowledge_service import DocumentKnowledgeService
from app.contracts.document_profile import DocumentProfile
from app.features.documents.application.interfaces.document_knowledge_pipeline import (
    DocumentKnowledgePipeline,
)


class DocumentKnowledgePipelineAdapter(DocumentKnowledgePipeline):
    """Adapter translating DocumentKnowledgePipeline interface calls to DocumentKnowledgeService."""

    def __init__(
        self, knowledge_service: DocumentKnowledgeService | None = None
    ) -> None:
        self._knowledge_service = (
            knowledge_service
            if knowledge_service is not None
            else DocumentKnowledgeService()
        )

    async def process_document_knowledge(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
    ) -> DocumentProfile:
        return await self._knowledge_service.process_document_knowledge(
            document_id=document_id,
            conversation_id=conversation_id,
            user_id=user_id,
            filename=filename,
            file_path=file_path,
        )

    async def delete_document_knowledge(
        self, document_id: uuid.UUID
    ) -> None:
        await self._knowledge_service.delete_document_knowledge(document_id)
