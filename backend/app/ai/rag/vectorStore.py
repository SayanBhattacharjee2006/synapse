from langchain_qdrant import QdrantVectorStore
from app.ai.rag.embeddings import embeddings
from app.core.config import settings
from app.ai.rag.client import client


def get_conversation_vector_store():
    conversation_vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_CONVERSATIONS_COLLECTION,
        embedding=embeddings,
    )
    return conversation_vector_store

def get_summary_vector_store():
    summary_vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_SUMMARIES_COLLECTION,
        embedding=embeddings,
    )
    return summary_vector_store

def get_document_vector_store():
    document_vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
        embedding=embeddings,
    )
    return document_vector_store

