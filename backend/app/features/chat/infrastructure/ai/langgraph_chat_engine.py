from typing import Any, AsyncIterator
import uuid

from langchain_core.messages import HumanMessage, SystemMessage
import langsmith as ls

from app.ai.llm import llm as default_llm
from app.core.logging import logger
from app.features.chat.application.interfaces.chat_engine import ChatEngine
from app.features.chat.application.models import ChatEvent

STATUS_BY_NODE = {
    "evaluator": {
        "status": "routing",
        "message": "Understanding your question...",
    },
    "retreiver": {
        "status": "searching_documents",
        "message": "Searching your uploaded documents...",
    },
    "web": {
        "status": "searching_web",
        "message": "Searching the web...",
    },
    "llm": {
        "status": "generating",
        "message": "Generating answer...",
    },
    "error": {
        "status": "error",
        "message": "Something went wrong while processing your request.",
    },
}


class LangGraphChatEngine(ChatEngine):
    """ChatEngine implementation wrapping the application-scoped compiled LangGraph graph."""

    def __init__(self, graph: Any, llm: Any = None) -> None:
        self._graph = graph
        self._llm = llm or default_llm

    async def stream_chat(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        has_uploaded_documents: bool,
    ) -> AsyncIterator[ChatEvent]:
        config = {"configurable": {"thread_id": str(conversation_id)}}
        metadata = {
            "conversation_id": str(conversation_id),
            "user_id": str(user_id),
            "has_uploaded_documents": has_uploaded_documents,
        }

        logger.bind(
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            has_uploaded_documents=has_uploaded_documents,
        ).info("chat.response.stream.started")

        summary = None
        retrieval_found = False
        retrieved_document_names: list[str] = []
        web_found = False
        web_sources: list[str] = []

        with ls.tracing_context(
            metadata=metadata,
            tags=["synapse", "chat"],
        ):
            async for event in self._graph.astream_events(
                {
                    "messages": [HumanMessage(content=content)],
                    "conversation_id": str(conversation_id),
                    "has_uploaded_documents": has_uploaded_documents,
                },
                config=config,
                version="v2",
            ):
                if event.get("event") == "on_chain_start":
                    node = event.get("metadata", {}).get("langgraph_node")
                    status = STATUS_BY_NODE.get(node)
                    if status:
                        yield ChatEvent(event_type="status", data=status)

                elif event.get("event") == "on_chain_end":
                    node = (
                        event.get("metadata", {}).get("langgraph_node")
                        or event.get("name")
                    )
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict):
                        if (
                            node == "summarisation"
                            or event.get("name") == "summarisation"
                        ):
                            summary = output.get("summary", "")

                        if (
                            node == "retreiver"
                            or event.get("name") == "retreiver"
                        ):
                            retrieval_found = output.get(
                                "retrieval_found", False
                            )
                            docs = (
                                output.get("retrieved_document_names")
                                or output.get("retieved_document_names")
                                or []
                            )
                            if isinstance(docs, list):
                                retrieved_document_names = docs

                        if node == "web" or event.get("name") == "web":
                            web_found = output.get("web_found", False)
                            urls = output.get("web_sources", [])
                            if isinstance(urls, list):
                                web_sources = urls

                elif (
                    event.get("event") == "on_chat_model_stream"
                    and event.get("metadata", {}).get("langgraph_node") == "llm"
                ):
                    chunk = event.get("data", {}).get("chunk")
                    token = (
                        chunk.content
                        if hasattr(chunk, "content")
                        else str(chunk or "")
                    )
                    if token:
                        yield ChatEvent(event_type="tokens", data=token)

        # Emit internal summary event if present
        if summary:
            yield ChatEvent(event_type="_summary", data={"summary": summary})

        # Emit retrieval_found if documents were retrieved
        if retrieval_found:
            yield ChatEvent(
                event_type="retrieval_found",
                data={"retrieved_doc_names": retrieved_document_names},
            )

        # Emit web_found if web sources were found
        if web_found:
            yield ChatEvent(
                event_type="web_found",
                data={"web_sources": web_sources},
            )

    async def generate_title(self, content: str) -> str:
        title_response = await self._llm.ainvoke(
            [
                SystemMessage(
                    content="You are a title generator. Generate a short title of maximum 5 words for this conversation. Return only the title, nothing else."
                ),
                HumanMessage(content=content),
            ]
        )
        return str(title_response.content).strip()

