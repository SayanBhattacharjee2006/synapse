from app.ai.rag.client import client
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client import models
from app.core.config import settings

dense_vector_config = VectorParams(size=1536, distance=Distance.COSINE)


async def create_collections():
    if not await client.collection_exists(settings.QDRANT_CONVERSATIONS_COLLECTION):

        await client.create_collection(
            collection_name=settings.QDRANT_CONVERSATIONS_COLLECTION,
            vectors_config=dense_vector_config,
        )

    if not await client.collection_exists(settings.QDRANT_SUMMARIES_COLLECTION):

        await client.create_collection(
            collection_name=settings.QDRANT_SUMMARIES_COLLECTION,
            vectors_config=dense_vector_config,
        )

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
                    hnsw_config=models.HnswConfigDiff(m=0)
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
            }
        )
