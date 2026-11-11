import uuid

from langchain_core.documents import Document as LangchainDocument

from app.ai.rag.embeddings import embed_chunks_in_batches
from app.ai.rag.ingestion.chunking import split_documents
from app.ai.rag.ingestion.loaders.factory import load_document
from app.ai.rag.vector_store.document_chunks import (
    build_chunk_points,
    upsert_document_chunks,
)
from app.core.logging import logger


async def load_and_chunk_document(
    document: object | None = None,
    file_path: str = "",
    document_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    filename: str | None = None,
) -> list[LangchainDocument]:
    """Load a document from disk and split it into LangChain document chunks with metadata."""
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
    """Generate dense, sparse and late-interaction embeddings and index chunks into Qdrant."""
    texts = [chunk.page_content for chunk in text_chunks]

    dense_vectors, sparse_vectors, multi_vectors = (
        await embed_chunks_in_batches(texts, 32)
    )

    points = build_chunk_points(
        text_chunks=text_chunks,
        dense_vectors=dense_vectors,
        sparse_vectors=sparse_vectors,
        multi_vectors=multi_vectors,
    )

    await upsert_document_chunks(points=points, batch_size=25)

