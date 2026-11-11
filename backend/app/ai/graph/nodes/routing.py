from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.graph.state import GraphState
from app.ai.llm import router_llm
from app.ai.prompts.chat import get_evaluator_prompt
from app.ai.schema import RouterType
from app.core.logging import logger


async def evaluator_node(state: GraphState) -> dict:
    query = state["messages"][-1].content

    has_uploaded_documents = state.get(
        "has_uploaded_documents",
        False,
    )

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        has_uploaded_documents=has_uploaded_documents,
    ).info("chat.evaluation.started")

    evaluator_prompt = get_evaluator_prompt(has_uploaded_documents)

    response = await router_llm.ainvoke(
        [
            SystemMessage(content=evaluator_prompt),
            HumanMessage(content=query),
        ]
    )

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        router=response.router.value,
        optimized_rag_query=response.rag_query,
        optimized_web_query=response.web_query,
    ).info("chat.evaluation.completed")

    return {
        "router": response.router,
        "optimized_rag_query": response.rag_query or query,
        "optimized_web_query": response.web_query or query,
    }


def route_after_evaluation(state: GraphState):
    decision = state.get("router", RouterType.NONE)

    if decision == RouterType.RAG:
        return ["doc_summary_retrieval"]
    elif decision == RouterType.WEB:
        return ["web"]
    elif decision == RouterType.BOTH:
        return ["doc_summary_retrieval"]
    elif decision == RouterType.NONE:
        return ["full_context_builder"]


def route_after_document_summary(state: GraphState):
    decision = state.get("router", RouterType.NONE)

    if decision == RouterType.RAG:
        return ["retreiver"]
    elif decision == RouterType.BOTH:
        return ["retreiver", "doc_aware_web_optimizer"]

