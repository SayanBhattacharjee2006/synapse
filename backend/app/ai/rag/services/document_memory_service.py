import uuid
from app.ai.rag.client import client
from app.core.config import settings
from qdrant_client import models

async def delete_document_chunks(documet_id: uuid.UUID):
    await client.delete(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=str(documet_id)),
                    )
                ]
            )
        )
    )