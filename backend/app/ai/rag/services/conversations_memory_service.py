from app.ai.rag.vectorStore import get_conversation_vector_store
from app.features.conversations.models import Message
from langchain_core.documents import Document
import uuid

def store_message(message: Message, user_id: uuid.UUID )-> None:
    document = Document(
        page_content=message.content,
        metadata={
            "sender": message.sender,
            "created_at": message.created_at.isoformat(),
            "conversation_id": str(message.conversation_id),
            "user_id": str(user_id),
            "message_id": str(message.id)
        },
    )

    get_conversation_vector_store().add_documents([document])