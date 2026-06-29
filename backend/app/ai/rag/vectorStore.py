from langchain_qdrant import QdrantVectorStore
from app.ai.rag.embeddings import dense_embeddings
from app.core.config import settings
from app.ai.rag.client import client


def get_conversation_vector_store():
    conversation_vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_CONVERSATIONS_COLLECTION,
        embedding=dense_embeddings,
    )
    return conversation_vector_store

def get_summary_vector_store():
    summary_vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_SUMMARIES_COLLECTION,
        embedding=dense_embeddings,
    )
    return summary_vector_store

# document handling is migrated to native qdrant from langchain so vector store for document is not required it directly works with the qdrant client 

# def get_document_vector_store():
#     document_vector_store = QdrantVectorStore(
#         client=client,
#         collection_name=settings.QDRANT_DOCUMENTS_COLLECTION,
#         embedding=dense_embeddings,
#     )
#     return document_vector_store

