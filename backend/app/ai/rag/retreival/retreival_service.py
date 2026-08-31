import asyncio
from app.ai.schema import DocumentSummarySchema
from app.ai.rag.client import client
from app.ai.rag.embeddings import (
    get_dense_embeddings,
    embed_sparse_query,
    embed_late_interaction_query,
)
from app.core.config import settings
from qdrant_client import models
from app.features.documents.dependency import create_context
from app.core.logging import logger


async def retrieve_document_summaries(
    query: str, conversation_id: str, k: int = 5
) -> list[DocumentSummarySchema]:
    
    logger.bind(conversation_id=conversation_id).info(
        "rag.document_summary.retrieval.started"
    )

    dense_vector = await get_dense_embeddings().aembed_query(query)
    sparse_vector = await asyncio.to_thread(embed_sparse_query, query)

    doc_sum_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="conversation_id",
                match=models.MatchValue(value=conversation_id),
            )
        ]
    )

    results = await client.query_points(
        collection_name=settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION,
        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using="dense",
                limit=20,
                filter=doc_sum_filter,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vector.indices.tolist(),
                    values=sparse_vector.values.tolist(),
                ),
                using="sparse",
                limit=20,
                filter=doc_sum_filter,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=doc_sum_filter,
        with_payload=True,
        limit=k,
    )

    logger.bind(
        conversation_id=conversation_id,
        document_count=len(results.points),
    ).info("rag.document_summary.retrieval.completed")

    if not results.points:
        logger.bind(conversation_id=conversation_id).warning(
            "rag.document_summary.retrieval.not_found"
        )
        return []

    return [
        DocumentSummarySchema(**document_summary.payload)
        for document_summary in results.points
    ]


async def retreive_context(
    query: str,
    document_summaries: list[DocumentSummarySchema],
    conversation_id: str,
    k: int = 5,
):
    # Embed the query 3 ways — dense (async HTTP), sparse + multi (CPU, off the event loop)

    retrieval_scope = "summary_scoped" if document_summaries else "conversation_scoped"

    logger.bind(
        conversation_id=conversation_id,
        retrieval_scope=retrieval_scope,
    ).info("rag.document_chunks.retrieval.started")

    dense_vector = await get_dense_embeddings().aembed_query(query)
    sparse_vector = await asyncio.to_thread(embed_sparse_query, query)
    multi_vector = await asyncio.to_thread(embed_late_interaction_query, query)

    if document_summaries:
        doc_chunk_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchAny(
                        any=[
                            str(document_summary.document_id)
                            for document_summary in document_summaries
                        ]
                    ),
                ),
            ]
        )
    else:
        doc_chunk_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="conversation_id",
                    match=models.MatchValue(value=conversation_id),
                ),
            ]
        )

    # Find the best matched Chunks from the filtered scope
    results = await client.query_points(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using="dense",
                limit=20,
                filter=doc_chunk_filter,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vector.indices.tolist(),
                    values=sparse_vector.values.tolist(),
                ),
                using="sparse",
                limit=20,
                filter=doc_chunk_filter,
            ),
        ],
        query=multi_vector.tolist(),
        using="multi",
        query_filter=doc_chunk_filter,
        with_payload=True,
        limit=k,
    )

    docs = results.points

    retrieved_document_names = list(
        dict.fromkeys(
            doc.payload["filename"] for doc in docs if doc.payload.get("filename")
        )
    )

    if not docs:
        logger.bind(
            conversation_id=conversation_id,
            retrieval_scope=retrieval_scope,
        ).warning("rag.document_chunks.not_found")
        return "", False, []

    best_score = docs[0].score
    logger.bind(
        conversation_id=conversation_id,
        retrieval_scope=retrieval_scope,
        result_count=len(docs),
        best_score=best_score,
    ).info("rag.document_chunks.retrieval.completed")

    if best_score < 0.3:
        logger.bind(
            conversation_id=conversation_id,
            best_score=best_score,
        ).warning("rag.retrieval.below_threshold")
        return "", False, []

    context = create_context(docs)

    return context, True, retrieved_document_names
