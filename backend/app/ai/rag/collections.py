from app.ai.rag.client import client
from qdrant_client.http.models import Distance, VectorParams
from app.core.config import settings

def create_collections():
    vector_config= VectorParams(size=1536, distance=Distance.COSINE)
    if not client.collection_exists(settings.QDRANT_CONVERSATIONS_COLLECTION):
        client.create_collection(
            collection_name=settings.QDRANT_CONVERSATIONS_COLLECTION,
            vectors_config=vector_config,
        )
    if not client.collection_exists(settings.QDRANT_SUMMARIES_COLLECTION):
        client.create_collection(
            collection_name=settings.QDRANT_SUMMARIES_COLLECTION,
            vectors_config=vector_config,
        )
    if not client.collection_exists(settings.QDRANT_DOCUMENTS_COLLECTION):
        client.create_collection(
            collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
            vectors_config=vector_config,
        )
