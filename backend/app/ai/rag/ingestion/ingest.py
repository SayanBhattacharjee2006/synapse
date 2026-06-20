from app.ai.rag.ingestion.loaders.factory import load_document
from app.ai.rag.ingestion.chunking import split_documents
from app.ai.rag.vectorStore import get_document_vector_store


async def ingest_document(document, file_path):

    documents = await load_document(file_path)

    for doc in documents:
        doc.metadata.update(
            {
                "document_id": str(document.id),
                "conversation_id": str(document.conversation_id),
                "user_id": str(document.user_id),
                "filename": document.filename,
            }
        )

    text_chunks = await split_documents(documents)

    vector_store = get_document_vector_store()

    await vector_store.aadd_documents(text_chunks)
