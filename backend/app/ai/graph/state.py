from langgraph.graph import MessagesState
from app.ai.schema import RouterType
from typing import List

class GraphState(MessagesState):
    summary: str = ""
    last_summarised_msg_id: str | None = None
    conversation_id: str

    retrieved_context: str = ""
    retrieval_found: bool = False
        
    web_context: str = ""
    web_sources: List[str] = []
    web_found: bool = False

    has_uploaded_documents: bool = False
    router: RouterType = RouterType.NONE

    optimized_rag_query: str = ""
    optimized_web_query: str = ""