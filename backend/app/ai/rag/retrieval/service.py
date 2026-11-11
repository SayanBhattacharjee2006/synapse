import asyncio

from app.ai.rag.embeddings import (
    embed_late_interaction_query,
    embed_sparse_query,
    get_dense_embeddings,
)
from app.ai.rag.retrieval.context_builder import build_context
from app.ai.rag.retrieval.schemas import DocumentSummarySchema
from app.ai.rag.vector_store.document_chunks import query_document_chunks
from app.ai.rag.vector_store.document_summaries import (
    query_document_summaries,
)
from app.core.logging import logger


async def retrieve_document_summaries(
    query: str, conversation_id: str, k: int = 5
) -> list[DocumentSummarySchema]:
    """Retrieve top-k relevant document summaries for a query within a conversation."""
    logger.bind(conversation_id=conversation_id).info(
        "rag.document_summary.retrieval.started"
    )

    dense_vector = await get_dense_embeddings().aembed_query(query)
    sparse_vector = await asyncio.to_thread(embed_sparse_query, query)

    results = await query_document_summaries(
        dense_vector=dense_vector,
        sparse_vector=sparse_vector,
        conversation_id=conversation_id,
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
) -> tuple[str, bool, list[str]]:
    """Retrieve relevant document chunks using hybrid vector search (dense + sparse + late-interaction).

    Returns a tuple of (context_text, success_bool, retrieved_source_filenames).
    """
    retrieval_scope = (
        "summary_scoped" if document_summaries else "conversation_scoped"
    )

    logger.bind(
        conversation_id=conversation_id,
        retrieval_scope=retrieval_scope,
    ).info("rag.document_chunks.retrieval.started")

    dense_vector = await get_dense_embeddings().aembed_query(query)
    sparse_vector = await asyncio.to_thread(embed_sparse_query, query)
    multi_vector = await asyncio.to_thread(embed_late_interaction_query, query)

    document_ids = (
        [
            str(summary.document_id)
            for summary in document_summaries
        ]
        if document_summaries
        else None
    )

    results = await query_document_chunks(
        dense_vector=dense_vector,
        sparse_vector=sparse_vector,
        multi_vector=multi_vector,
        document_ids=document_ids,
        conversation_id=conversation_id,
        limit=k,
    )

    docs = results.points

    retrieved_document_names = list(
        dict.fromkeys(
            doc.payload["filename"]
            for doc in docs
            if doc.payload and doc.payload.get("filename")
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

    context = build_context(docs)

    return context, True, retrieved_document_names


# Compatibility alias
retrieve_context = retreive_context

