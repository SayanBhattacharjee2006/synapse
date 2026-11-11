from qdrant_client import models
from qdrant_client.http.models import Distance

from app.ai.rag.vector_store.client import client
from app.core.config import settings


async def create_collections() -> None:
    """Initialize required Qdrant collections.

    Only document chunks and document summaries collections are created.
    Legacy conversation-summary collections are intentionally omitted.
    """
    if not await client.collection_exists(settings.QDRANT_DOCUMENTS_COLLECTION):
        await client.create_collection(
            collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
            vectors_config={
                "dense": models.VectorParams(
                    size=1536, distance=models.Distance.COSINE
                ),
                "multi": models.VectorParams(
                    size=96,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                    hnsw_config=models.HnswConfigDiff(m=0),
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            },
        )

    if not await client.collection_exists(
        settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION
    ):
        await client.create_collection(
            collection_name=settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION,
            vectors_config={
                "dense": models.VectorParams(
                    size=1536, distance=Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            },
        )

