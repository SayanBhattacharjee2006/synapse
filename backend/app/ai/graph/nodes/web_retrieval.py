from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.graph.state import GraphState
from app.ai.llm import llm
from app.ai.prompts.chat import get_document_aware_web_query_optimizer_prompt
from app.ai.schema import DocumentAwareWebQuerySchema
from app.core.logging import logger
from app.integretions.taviily.tavily import (
    create_search_response,
    search_tavily,
)


async def document_aware_web_query_optimizer_node(state: GraphState) -> dict:
    optimized_web_query = state.get("optimized_web_query", "")
    if not optimized_web_query:
        optimized_web_query = next(
            (
                message.content
                for message in reversed(state["messages"])
                if isinstance(message, HumanMessage)
            ),
            state["messages"][-1].content,
        )

    document_summaries = state.get("document_summaries", [])
    conversation_id = str(state.get("conversation_id", ""))
    logger.bind(conversation_id=conversation_id).info(
        "web.document_aware_query.optimization.started"
    )

    if not document_summaries:
        logger.bind(
            conversation_id=conversation_id,
            document_summary_count=0,
            generated_query=optimized_web_query,
        ).info("web.document_aware_query.optimization.completed")
        return {"document_aware_web_query": optimized_web_query}

    try:
        prompt = get_document_aware_web_query_optimizer_prompt(
            optimized_web_query=optimized_web_query,
            document_summaries=document_summaries,
        )
        response = await llm.with_structured_output(
            DocumentAwareWebQuerySchema
        ).ainvoke([SystemMessage(content=prompt)])
        document_aware_web_query = (response.web_query or "").strip()
        if not document_aware_web_query:
            document_aware_web_query = optimized_web_query

        logger.bind(
            conversation_id=conversation_id,
            document_summary_count=len(document_summaries),
            generated_query=document_aware_web_query,
        ).info("web.document_aware_query.optimization.completed")
        return {"document_aware_web_query": document_aware_web_query}
    except Exception:
        logger.bind(conversation_id=conversation_id).exception(
            "web.document_aware_query.optimization.failed"
        )
        return {"document_aware_web_query": optimized_web_query}


async def web_retreival_node(state: GraphState) -> dict:
    document_aware_web_query = state.get("document_aware_web_query", "")
    optimized_web_query = state.get("optimized_web_query", "")
    query = document_aware_web_query or optimized_web_query
    if not query:
        query = next(
            (
                message.content
                for message in reversed(state["messages"])
                if isinstance(message, HumanMessage)
            ),
            state["messages"][-1].content,
        )

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        query=query,
    ).info("web.retrieval.started")

    try:
        response = await search_tavily(query)

        results = response.get("results", [])
        context = create_search_response(response)

        web_sources = [
            result["url"] for result in results if result.get("url")
        ]

        web_found = bool(context)

        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
            result_count=len(results),
        ).info("web.retrieval.completed")

        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
            result_count=len(results),
            web_found=web_found,
            sources_count=len(web_sources),
        ).info("web.retrieval.state")

        if not context:
            return {
                "web_context": "",
                "web_found": False,
                "web_sources": [],
            }

        return {
            "web_context": context,
            "web_found": web_found,
            "web_sources": web_sources,
        }

    except KeyError as e:
        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
            error_reason=str(e),
        ).warning("web.retrieval.failed")

    except Exception:
        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
        ).exception("web.retrieval.failed")

    return {
        "web_context": "",
        "web_found": False,
        "web_sources": [],
    }

