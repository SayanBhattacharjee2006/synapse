from app.ai.rag.retreival.retreival_service import retreive_context
from app.ai.prompts.chat import (
    get_summariser_prompt,
    get_system_prompt,
    get_evaluator_prompt,
    get_query_optimizer_prompt,
)
from app.ai.graph.state import GraphState
from langchain_core.messages import (
    SystemMessage,
    RemoveMessage,
    HumanMessage,
    AIMessage,
)
from langchain_core.messages.utils import count_tokens_approximately
from app.ai.llm import llm, structured_llm, optimized_query_llm
from app.ai.schema import RouterType
from app.integretions.taviily.tavily import search_tavily, create_search_response
from app.core.logging import logger


async def llm_node(state: GraphState) -> dict:
    summary = state.get("summary", "")
    retrieved_context = state.get("retrieved_context", "")
    retrieval_found = state.get("retrieval_found", False)
    web_context = state.get("web_context", "")
    web_found = state.get("web_found", False)
    router = state.get("router", RouterType.NONE)

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        router=str(router),
        retrieval_found=retrieval_found,
        web_found=web_found,
    ).info("chat.llm.started")



    system_prompt = get_system_prompt(
        summary=summary,
        retrieved_context=retrieved_context,
        retrieval_found=retrieval_found,
        web_context=web_context,
        web_found=web_found,
        router=router,
    )

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    res = await llm.ainvoke(messages)

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        router=str(router),
    ).info("chat.llm.completed")

    return {
        "messages": [res],
    }


async def summarisation_node(state: GraphState) -> dict:
    tokensCount = count_tokens_approximately(state["messages"])
    if tokensCount < 2500:
        return {}
    else:
        if state.get("last_summarised_msg_id", "") is None:
            last_summarised_msg_idx = 0
        else:
            last_summarised_msg_idx = next(
                (
                    idx
                    for idx, msg in enumerate(state["messages"])
                    if msg.id == state.get("last_summarised_msg_id", "")
                ),
                None,
            )

        if last_summarised_msg_idx is None:
            last_summarised_msg_idx = 0

        messges_to_summarise = state["messages"][
            last_summarised_msg_idx + 1 : len(state["messages"]) - 10
        ]

        if not messges_to_summarise:
            return {}

        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
            token_count=tokensCount,
            message_count=len(messges_to_summarise),
        ).info("chat.summary.started")

        summary_respone = await llm.ainvoke(
            [
                SystemMessage(
                    content=get_summariser_prompt(
                        state.get("summary", ""), messges_to_summarise
                    )
                )
            ]
        )
        messages_to_remove = state["messages"][:-10]
        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
            token_count=tokensCount,
            message_count=len(messges_to_summarise),
        ).info("chat.summary.completed")
        return {
            "summary": summary_respone.content,
            "last_summarised_msg_id": messges_to_summarise[-1].id,
            "messages": [RemoveMessage(id=msg.id) for msg in messages_to_remove],
        }


async def retreive_context_node(state: GraphState) -> dict:
    query = state.get("optimized_rag_query", state["messages"][-1].content)
    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
    ).info("rag.retrieval.started")

    context, success = await retreive_context(
        query=query, conversation_id=str(state.get("conversation_id", ""))
    )

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        retrieval_found=success,
    ).info("rag.retrieval.completed")
    return {"retrieved_context": context, "retrieval_found": success}


async def evaluator_node(state: GraphState) -> dict:

    query = state["messages"][-1].content

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        has_uploaded_documents=state.get("has_uploaded_documents", False),
    ).info("chat.evaluation.started")
    evaluator_prompt = get_evaluator_prompt(state.get("has_uploaded_documents", False))

    response = await structured_llm.ainvoke(
        [SystemMessage(content=evaluator_prompt), HumanMessage(content=query)]
    )

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        router=str(response.router),
    ).info("chat.evaluation.completed")
    return {
        "router": response.router,
    }


def route_after_evaluation(state: GraphState):
    decision = state.get("router", "none")

    if decision == RouterType.RAG:
        return ["retreiver"]
    elif decision == RouterType.WEB:
        return ["web"]
    elif decision == RouterType.BOTH:
        return ["retreiver", "web"]
    elif decision == RouterType.NONE:
        return ["llm"]


async def web_retreival_node(state: GraphState) -> dict:
    query = state.get("optimized_web_query", state["messages"][-1].content)
    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
    ).info("web.retrieval.started")
    try:

        response = await search_tavily(query)

        context = create_search_response(response)
        if not context:
            logger.bind(
                conversation_id=str(state.get("conversation_id", "")),
                result_count=len(response.get("results", [])),
            ).info("web.retrieval.completed")
            return {"web_context": "", "web_found": False, "web_sources": []}
        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
            result_count=len(response.get("results", [])),
        ).info("web.retrieval.completed")
        if state.get("router", RouterType.NONE) == RouterType.BOTH:
            return {
                "web_context": context,
                "web_found": bool(response["results"]),
                "web_sources": [result["url"] for result in response["results"]],
            }
        else:
            return {
                "web_context": context,
                "web_found": bool(response["results"]),
                "web_sources": [],
                "retrieved_context": context,
                "retrieval_found": False,
            }
    except KeyError as e:
        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
            error_reason=str(e),
        ).warning("web.retrieval.failed")
    except Exception as e:
        logger.bind(
            conversation_id=str(state.get("conversation_id", "")),
        ).exception("web.retrieval.failed")
    return {"web_context": "", "web_found": False, "web_sources": []}


async def query_optimizer_node(state: GraphState) -> dict:
    query = state["messages"][-1].content
    router = state.get("router", RouterType.NONE)
    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        router=str(router),
    ).info("chat.query_optimization.started")
    optimizer_prompt = get_query_optimizer_prompt()

    response = await optimized_query_llm.ainvoke(
        [
            SystemMessage(content=optimizer_prompt),
            HumanMessage(content=f"Router Decision: {router} \n user query: {query}"),
        ]
    )

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        router=str(router),
    ).info("chat.query_optimization.completed")

    return {
        "optimized_rag_query": response.rag_query,
        "optimized_web_query": response.web_query,
    }
