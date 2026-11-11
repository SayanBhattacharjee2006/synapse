from typing import Any
import uuid

from langchain_core.documents import Document as LangchainDocument
from qdrant_client import models

from app.ai.rag.vector_store.client import client
from app.core.config import settings
from app.core.logging import logger


def build_chunk_points(
    text_chunks: list[LangchainDocument],
    dense_vectors: list[list[float]],
    sparse_vectors: list[Any],
    multi_vectors: list[Any],
) -> list[models.PointStruct]:
    """Create Qdrant PointStruct instances for document chunks."""
    return [
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


async def upsert_document_chunks(
    points: list[models.PointStruct], batch_size: int = 25
) -> None:
    """Upsert chunk points into the document chunks collection in batches."""
    logger.bind(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        points_upserted=len(points),
    ).info("qdrant.documents.upsert.started")

    for i in range(0, len(points), batch_size):
        await client.upsert(
            collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
            points=points[i : i + batch_size],
        )

    logger.bind(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        points_upserted=len(points),
    ).info("qdrant.documents.upsert.completed")


async def delete_document_chunks(document_id: uuid.UUID) -> None:
    """Delete all chunks belonging to a document from Qdrant."""
    await client.delete(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=str(document_id)),
                    )
                ]
            )
        ),
    )


async def query_document_chunks(
    dense_vector: list[float],
    sparse_vector: Any,
    multi_vector: Any,
    query_filter: models.Filter,
    limit: int = 5,
) -> Any:
    """Execute hybrid vector search across document chunks with prefetch and late-interaction reranking."""
    return await client.query_points(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
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
        query=multi_vector.tolist(),
        using="multi",
        query_filter=query_filter,
        with_payload=True,
        limit=limit,
    )

