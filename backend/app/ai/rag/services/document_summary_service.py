import asyncio
from app.core.config import settings
from app.features.documents.summary.schemas import DocumentProfile
from app.ai.rag.embeddings import embed_sparse_query, get_dense_embeddings
from app.ai.rag.client import client
from app.features.documents.formatter import format_document_profile
from qdrant_client import models

from app.features.documents.model import Document

async def store_document_summary(doc: Document,document_profile: DocumentProfile)-> None: 

    formatted_document_profile = format_document_profile(document_profile)

    dense_vector, sparse_vector = await asyncio.gather(
        get_dense_embeddings().aembed_query(formatted_document_profile),
        asyncio.to_thread(embed_sparse_query, formatted_document_profile),
    )

    await client.upsert(
        collection_name = settings.QDRANT_DOCUMENT_SUMMARY_COLLECTION,
        points = [
            models.PointStruct(
                id = str(doc.id),
                vector = {
                    "dense": dense_vector,
                    "sparse": models.SparseVector(
                        indices = sparse_vector.indices.tolist(),
                        values = sparse_vector.values.tolist()
                    )
                },
                payload = {
                    "document_id": str(doc.id),
                    "conversation_id": str(doc.conversation_id),
                    "user_id": str(doc.user_id),
                    "filename": doc.filename,
                    "summary": document_profile.summary,
                    "topics": document_profile.topics
                }
            )
        ]
    )