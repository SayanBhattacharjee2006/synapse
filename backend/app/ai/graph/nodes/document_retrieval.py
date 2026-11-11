from langchain_core.messages import HumanMessage

from app.ai.graph.state import GraphState
from app.ai.rag.retrieval.service import (
    retreive_context,
    retrieve_document_summaries,
)
from app.core.logging import logger


async def document_summary_retrieval_node(state: GraphState) -> dict:
    query = state.get("optimized_rag_query", "")
    if not query:
        query = next(
            (
                message.content
                for message in reversed(state["messages"])
                if isinstance(message, HumanMessage)
            ),
            state["messages"][-1].content,
        )

    conversation_id = str(state.get("conversation_id", ""))
    logger.bind(conversation_id=conversation_id).info(
        "rag.document_summary.retrieval.started"
    )

    try:
        summaries = await retrieve_document_summaries(query, conversation_id)
        document_summary_names = list(
            dict.fromkeys(
                summary.filename for summary in summaries if summary.filename
            )
        )

        logger.bind(
            conversation_id=conversation_id,
            document_count=len(summaries),
            document_summary_found=bool(summaries),
        ).info("rag.document_summary.retrieval.completed")

        return {
            "document_summaries": summaries,
            "document_summary_found": bool(summaries),
            "document_summary_names": document_summary_names,
        }
    except Exception:
        logger.bind(conversation_id=conversation_id).exception(
            "rag.document_summary.retrieval.failed"
        )
        return {
            "document_summaries": [],
            "document_summary_found": False,
            "document_summary_names": [],
        }


async def retreive_context_node(state: GraphState) -> dict:
    query = state.get("optimized_rag_query", state["messages"][-1].content)
    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
    ).info("rag.retrieval.started")

    context, success, retrieved_sources = await retreive_context(
        query=query,
        document_summaries=state.get("document_summaries", []),
        conversation_id=str(state.get("conversation_id", "")),
    )

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        retrieval_found=success,
    ).info("rag.retrieval.completed")
    return {
        "retrieved_context": context,
        "retrieval_found": success,
        "retrieved_document_names": retrieved_sources,
        "retieved_document_names": retrieved_sources,
    }

