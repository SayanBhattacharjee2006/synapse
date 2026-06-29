import asyncio
from app.ai.rag.client import client
from app.ai.rag.embeddings import (
    dense_embeddings,
    embed_sparse_query,
    embed_late_interaction_query,
)
from app.core.config import settings
from qdrant_client import models
from app.features.documents.dependency import create_context

async def retreive_context(query: str, conversation_id: str, k: int = 5):
    # Embed the query 3 ways — dense (async HTTP), sparse + multi (CPU, off the event loop)
    dense_vector = await dense_embeddings.aembed_query(query)
    sparse_vector = await asyncio.to_thread(embed_sparse_query, query)
    multi_vector = await asyncio.to_thread(embed_late_interaction_query, query)

    conversation_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="conversation_id",
                match=models.MatchValue(value=conversation_id),
            )
        ]
    )

    results = await client.query_points(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using="dense",
                limit=20,
                filter=conversation_filter,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vector.indices.tolist(),
                    values=sparse_vector.values.tolist(),
                ),
                using="sparse",
                limit=20,
                filter=conversation_filter,
            ),
        ],
        query=multi_vector.tolist(),
        using="multi",
        filter=conversation_filter,
        with_payload=True,
        limit=k,
    )

    docs = results.points

    if not docs:
        return "", False

    best_score = docs[0].score
    print("BEST SCORE : ", best_score)

    for doc in docs:
        print("DOC ID : ", doc.id)
        print("SCORE : ", doc.score)
        print("chunk: ", doc.payload.get("page_content"), "\n\n")

    if best_score < 0.4:
        return "", False

    context = create_context(docs)

    return context, True