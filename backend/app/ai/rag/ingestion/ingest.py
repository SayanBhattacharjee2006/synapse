import uuid
from langchain_core.documents import Document as LangchainDocument
from qdrant_client import models

from app.ai.rag.client import client
from app.ai.rag.embeddings import embed_chunks_in_batches
from app.ai.rag.ingestion.chunking import split_documents
from app.ai.rag.ingestion.loaders.factory import load_document
from app.core.config import settings
from app.core.logging import logger


async def load_and_chunk_document(
    document: object | None = None,
    file_path: str = "",
    document_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    filename: str | None = None,
) -> list[LangchainDocument]:
    doc_id = getattr(document, "id", None) or document_id
    convo_id = getattr(document, "conversation_id", None) or conversation_id
    u_id = getattr(document, "user_id", None) or user_id
    f_name = getattr(document, "filename", None) or filename or ""

    logger.bind(
        document_id=str(doc_id),
        conversation_id=str(convo_id),
        user_id=str(u_id),
        filename=f_name,
    ).info("document.load.started")

    documents = await load_document(file_path)

    logger.bind(
        document_id=str(doc_id),
        filename=f_name,
        documents_loaded=len(documents),
    ).info("document.load.completed")

    for doc in documents:
        doc.metadata.clear()
        doc.metadata.update(
            {
                "document_id": str(doc_id),
                "conversation_id": str(convo_id),
                "user_id": str(u_id),
                "filename": f_name,
            }
        )

    text_chunks = await split_documents(documents)
    logger.bind(
        document_id=str(doc_id),
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
