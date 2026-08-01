import uuid
from datetime import datetime, timezone 
from app.ai.rag.client import client
from app.ai.rag.embeddings import get_dense_embeddings
from qdrant_client import models
from app.core.config import settings

async def store_summary(summary:str, conversationId: uuid.UUID, user_id: uuid.UUID )-> None:
    dense_vector = await get_dense_embeddings().aembed_query(summary)
    point = models.PointStruct(
        id=str(conversationId),
        vector=dense_vector,
        payload={
            "summary": summary,
            "conversation_id": str(conversationId),
            "user_id": str(user_id),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    )

    await client.upsert(
        collection_name=settings.QDRANT_SUMMARIES_COLLECTION,
        points=[point]
    )
    