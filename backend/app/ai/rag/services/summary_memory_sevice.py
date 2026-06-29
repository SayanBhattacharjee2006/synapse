import uuid
from datetime import datetime, timezone 
from app.ai.rag.vectorStore import get_summary_vector_store
from langchain_core.documents import Document

async def store_summary(summary:str, conversationId: uuid.UUID, user_id: uuid.UUID )-> None:
    document = Document(
        page_content=summary,
        metadata={
            "conversation_id": str(conversationId),
            "user_id": str(user_id),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    await get_summary_vector_store().add_documents([document])