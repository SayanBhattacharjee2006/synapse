from langchain_core.messages import SystemMessage

from app.ai.graph.state import GraphState
from app.ai.llm import llm
from app.ai.prompts.chat import get_system_prompt
from app.ai.schema import RouterType
from app.core.logging import logger


async def full_context_builder_node(state: GraphState) -> dict:
    router = state.get("router", RouterType.NONE)
    retrieved_context = state.get("retrieved_context", "")
    web_context = state.get("web_context", "")
    conversation_id = str(state.get("conversation_id", ""))

    logger.bind(
        conversation_id=conversation_id,
        router=router.value,
        has_retrieved_context=bool(retrieved_context),
        has_web_context=bool(web_context),
    ).info("context.builder.started")

    if router == RouterType.NONE:
        full_context = ""

    elif router == RouterType.RAG:
        full_context = (
            f"DOCUMENT KNOWLEDGE BASE:\n{retrieved_context}"
            if retrieved_context
            else ""
        )

    elif router == RouterType.WEB:
        full_context = (
            f"WEB KNOWLEDGE BASE:\n{web_context}" if web_context else ""
        )

    elif router == RouterType.BOTH:
        parts = []
        if retrieved_context:
            parts.append(f"DOCUMENT KNOWLEDGE BASE:\n{retrieved_context}")
        if web_context:
            parts.append(f"WEB KNOWLEDGE BASE:\n{web_context}")
        full_context = "\n\n".join(parts)

    else:
        full_context = ""

    logger.bind(
        conversation_id=conversation_id,
        router=router.value,
        full_context_length=len(full_context),
    ).info("context.builder.completed")

    return {"full_context": full_context}


async def llm_node(state: GraphState) -> dict:
    summary = state.get("summary", "")
    full_context = state.get("full_context", "")
    router = state.get("router", RouterType.NONE)

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        router=router.value,
        has_full_context=bool(full_context),
        full_context_length=len(full_context),
    ).info("chat.llm.started")

    system_prompt = get_system_prompt(
        summary=summary,
        full_context=full_context,
        router=router.value.upper(),
    )

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    res = await llm.ainvoke(messages)

    logger.bind(
        conversation_id=str(state.get("conversation_id", "")),
        router=router.value,
    ).info("chat.llm.completed")

    return {
        "messages": [res],
    }

