import uuid
from qdrant_client import models
from app.ai.rag.vectorStore import get_document_vector_store
from app.features.documents.dependency import create_context

async def retreive_context(query: str, conversation_id: str, k: int = 5):
    document_vector_store = get_document_vector_store()

    docs = await document_vector_store.asimilarity_search_with_score(
        query=query,
        k=k,
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.conversation_id",
                    match=models.MatchValue(value=conversation_id),
                )
            ]
        ),
    )

    if not docs:
        return "",False 
    
    best_score = docs[0][1]
    print("BEST SCORE : ", best_score)

    for doc, score in docs:
        print("DOC ID : ", doc.id)
        print("SCORE : ", score)
        print("chunk: ", doc.page_content,"\n\n")

    if best_score < 0.4:
        return "",False
    
    context = create_context(docs)

    return context, True
