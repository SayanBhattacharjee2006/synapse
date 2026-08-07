import uuid
from app.ai.rag.ingestion.loaders.factory import load_document
from app.ai.rag.ingestion.chunking import split_documents
from app.ai.rag.embeddings import (
    embed_chunks_in_batches,
)
from app.core.config import settings
from qdrant_client import models
from app.ai.rag.client import client
from langchain_core.documents import Document as LangchainDocument
from app.features.documents.model import Document as ModelDocument
from app.core.logging import logger


async def load_and_chunk_document(
    document: ModelDocument, file_path: str
) -> list[LangchainDocument]:

    logger.bind(
        document_id=str(document.id),
        conversation_id=str(document.conversation_id),
        user_id=str(document.user_id),
        filename=document.filename,
    ).info("document.load.started")

    documents = await load_document(file_path)

    logger.bind(
        document_id=str(document.id),
        filename=document.filename,
        documents_loaded=len(documents),
    ).info("document.load.completed")

    for doc in documents:
        doc.metadata.clear()
        doc.metadata.update(
            {
                "document_id": str(document.id),
                "conversation_id": str(document.conversation_id),
                "user_id": str(document.user_id),
                "filename": document.filename,
            }
        )

    text_chunks = await split_documents(documents)
    logger.bind(
        document_id=str(document.id),
        chunk_count=len(text_chunks),
    ).info("document.chunking.completed")

    return text_chunks


async def ingest_document(text_chunks: list[LangchainDocument]) -> None:

    texts = [chunk.page_content for chunk in text_chunks]

    dense_vectors, sparse_vectors, multi_vectors = await embed_chunks_in_batches(
        texts, 32
    )

    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "dense": dense_vectors[i],
                "sparse": models.SparseVector(
                    indices=sparse_vectors[i].indices.tolist(),
                    values=sparse_vectors[i].values.tolist(),
                ),
                "multi": multi_vectors[i].tolist(),
            },
            payload={
                "page_content": text_chunks[i].page_content,
                **text_chunks[i].metadata,
            },
        )
        for i in range(len(text_chunks))
    ]

    logger.bind(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        points_upserted=len(points),
    ).info("qdrant.documents.upsert.started")

    BATCH_SIZE = 25

    for i in range(0, len(points), BATCH_SIZE):
        await client.upsert(
            collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
            points=points[i : i + BATCH_SIZE],
        )

    logger.bind(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        points_upserted=len(points),
    ).info("qdrant.documents.upsert.completed")
