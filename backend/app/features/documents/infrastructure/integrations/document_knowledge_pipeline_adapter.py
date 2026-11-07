import asyncio
import uuid

from app.ai.rag.ingestion.ingest import (
    ingest_document,
    load_and_chunk_document,
)
from app.ai.rag.services.document_memory_service import (
    delete_document_chunks,
)
from app.ai.rag.services.document_summary_service import (
    delete_document_summary,
    store_document_summary,
)
from app.ai.rag.summarization.schemas import DocumentProfile
from app.ai.rag.summarization.service import generate_document_profile
from app.core.logging import logger
from app.features.documents.application.interfaces.document_knowledge_pipeline import (
    DocumentKnowledgePipeline,
)


class DocumentKnowledgePipelineAdapter(DocumentKnowledgePipeline):

    async def process_document_knowledge(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
    ) -> DocumentProfile:
        logger.bind(
            document_id=str(document_id),
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            filename=filename,
        ).info("knowledge_pipeline.indexing.started")

        text_chunks = await load_and_chunk_document(
            file_path=file_path,
            document_id=document_id,
            conversation_id=conversation_id,
            user_id=user_id,
            filename=filename,
        )

        # Ingest text chunks and generate algorithmic summary profile concurrently
        _, doc_profile = await asyncio.gather(
            ingest_document(text_chunks),
            generate_document_profile(text_chunks),
        )

        # Store summary vector embedding in Qdrant summary collection
        await store_document_summary(
            document_id=document_id,
            conversation_id=conversation_id,
            user_id=user_id,
            filename=filename,
            document_profile=doc_profile,
        )

        logger.bind(
            document_id=str(document_id),
            chunks=len(text_chunks),
        ).info("knowledge_pipeline.indexing.completed")

        return doc_profile

    async def delete_document_knowledge(
        self, document_id: uuid.UUID
    ) -> None:
        logger.bind(document_id=str(document_id)).info(
            "knowledge_pipeline.deletion.started"
        )
        # Delete both chunks and summary vectors in Qdrant without swallowing exceptions
        await delete_document_chunks(document_id)
        await delete_document_summary(document_id)

        logger.bind(document_id=str(document_id)).info(
            "knowledge_pipeline.deletion.completed"
        )
