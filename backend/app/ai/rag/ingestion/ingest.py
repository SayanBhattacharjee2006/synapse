from app.ai.rag.ingestion.loaders.factory import load_document
from app.ai.rag.ingestion.chunking import split_documents
from app.ai.rag.vectorStore import get_document_vector_store


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

    vector_store = get_document_vector_store()

    print(f"Adding {len(text_chunks)} chunks to vector store...")

    await vector_store.aadd_documents(text_chunks)
