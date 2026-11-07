import asyncio
from types import SimpleNamespace
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
)
from app.core.logging import logger
from app.features.documents.application.interfaces.document_knowledge_pipeline import (
    DocumentKnowledgePipeline,
)
from app.features.documents.summary.service import (
    execute_doc_summary_pipeline,
)


class DocumentKnowledgePipelineAdapter(DocumentKnowledgePipeline):

    async def process_document_knowledge(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
    ) -> None:
        doc_meta = SimpleNamespace(
            id=document_id,
            conversation_id=conversation_id,
            user_id=user_id,
            filename=filename,
        )

        logger.bind(
            document_id=str(document_id),
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            filename=filename,
        ).info("knowledge_pipeline.indexing.started")

        text_chunks = await load_and_chunk_document(doc_meta, file_path)

        await asyncio.gather(
            ingest_document(text_chunks),
            execute_doc_summary_pipeline(
                text_chunks, document_id, conversation_id, user_id
            ),
        )

        logger.bind(
            document_id=str(document_id),
            chunks=len(text_chunks),
        ).info("knowledge_pipeline.indexing.completed")

    async def delete_document_knowledge(
        self, document_id: uuid.UUID
    ) -> None:
        logger.bind(document_id=str(document_id)).info(
            "knowledge_pipeline.deletion.started"
        )
        # Idempotent deletion across both collections
        try:
            await delete_document_chunks(document_id)
        except Exception:
            logger.bind(document_id=str(document_id)).warning(
                "knowledge_pipeline.delete_chunks.ignored_failure"
            )

        try:
            await delete_document_summary(document_id)
        except Exception:
            logger.bind(document_id=str(document_id)).warning(
                "knowledge_pipeline.delete_summary.ignored_failure"
            )

        logger.bind(document_id=str(document_id)).info(
            "knowledge_pipeline.deletion.completed"
        )

