import uuid
import asyncio
from app.ai.rag.ingestion.loaders.factory import load_document
from app.ai.rag.ingestion.chunking import split_documents
from app.ai.rag.embeddings import (
    embed_chunks_in_batches,
)

from app.core.config import settings
from qdrant_client import models


async def ingest_document(document, file_path):
    print(f"Ingesting document {document.filename}...")

    documents = await load_document(file_path)

    print(f"Loaded {len(documents)} documents from {document.filename}...")

    for doc in documents:
        doc.metadata.clear()
        doc.metadata.update(
            {
                "document_id": str(document.id),
                "conversation_id": str(document.conversation_id),
                "user_id": str(document.user_id),
                "filename": document.filename,
            }
        )

    print(f"Added document metadata to {len(documents)} documents...")

    text_chunks = await split_documents(documents)

    print(f"Split {len(documents)} documents into {len(text_chunks)} chunks...")

    texts = [chunk.page_content for chunk in text_chunks]

    print(f"Embedding {len(texts)} chunks (dense + multi + late) ...")

    dense_vectors, sparse_vectors, multi_vectors = await embed_chunks_in_batches(texts, batch_size=32)

    points = [
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
            }
        )
        for i in range(len(text_chunks))
    ]

    print(f"Upserting {len(points)} chunks to Qdrant...")

    await client.upsert(
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        points=points,
        batch_size=25,
    )

    print(f"Ingestion of {document.filename} completed...")