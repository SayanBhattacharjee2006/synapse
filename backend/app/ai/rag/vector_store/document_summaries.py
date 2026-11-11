import asyncio
from typing import Any
import uuid

from qdrant_client import models

from app.ai.rag.embeddings import embed_sparse_query, get_dense_embeddings
from app.ai.rag.summarization.formatter import format_document_profile
from app.ai.rag.summarization.schemas import DocumentProfile
from app.ai.rag.vector_store.client import client
from app.core.config import settings
from app.core.logging import logger


async def store_document_summary(
    document_id: uuid.UUID | object,
    conversation_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    filename: str | None = None,
    document_profile: DocumentProfile | None = None,
) -> None:
    """Embed and store a document profile in the document summaries Qdrant collection."""
    # Support backward-compatible duck-typing if first arg is an object with .id
    if hasattr(document_id, "id") and hasattr(document_id, "conversation_id"):
        doc_obj = document_id
        actual_profile = conversation_id  # 2nd arg was document_profile
        doc_id = doc_obj.id
        convo_id = doc_obj.conversation_id
        u_id = doc_obj.user_id
        f_name = doc_obj.filename
        profile = actual_profile
    else:
        doc_id = document_id
        convo_id = conversation_id
        u_id = user_id
        f_name = filename or ""
        profile = document_profile

    logger.bind(
        document_id=str(doc_id),
        conversation_id=str(convo_id),
        collection_name=settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION,
        points_upserted=1,
    ).info("qdrant.summary.upsert.started")

    formatted_document_profile = format_document_profile(profile)

    dense_vector, sparse_vector = await asyncio.gather(
        get_dense_embeddings().aembed_query(formatted_document_profile),
        asyncio.to_thread(embed_sparse_query, formatted_document_profile),
    )

    await client.upsert(
        collection_name=settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION,
        points=[
            models.PointStruct(
                id=str(doc_id),
                vector={
                    "dense": dense_vector,
                    "sparse": models.SparseVector(
                        indices=sparse_vector.indices.tolist(),
                        values=sparse_vector.values.tolist(),
                    ),
                },
                payload={
                    "document_id": str(doc_id),
                    "conversation_id": str(convo_id),
                    "user_id": str(u_id),
                    "filename": f_name,
                    "summary": profile.summary if profile else None,
                    "topics": profile.topics if profile else None,
                },
            )
        ],
    )

    logger.bind(
        document_id=str(doc_id),
        conversation_id=str(convo_id),
        collection_name=settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION,
        points_upserted=1,
    ).info("qdrant.summary.upsert.completed")


async def delete_document_summary(document_id: uuid.UUID) -> None:
    """Delete a document summary from Qdrant by document ID."""
    await client.delete(
        collection_name=settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION,
        points_selector=models.PointIdsList(points=[str(document_id)]),
    )


async def query_document_summaries(
    dense_vector: list[float],
    sparse_vector: Any,
    query_filter: models.Filter,
    limit: int = 5,
) -> Any:
    """Execute hybrid vector search across document summaries with RRF fusion."""
    return await client.query_points(
        collection_name=settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION,
        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using="dense",
                limit=20,
                filter=query_filter,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vector.indices.tolist(),
                    values=sparse_vector.values.tolist(),
                ),
                using="sparse",
                limit=20,
                filter=query_filter,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=query_filter,
        with_payload=True,
        limit=limit,
    )

