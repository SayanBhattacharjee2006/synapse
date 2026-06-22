from app.ai.rag.retreival.retreival_service import retreive_context
from app.ai.prompts.chat import get_summariser_prompt, get_system_prompt, get_evaluator_prompt
from app.ai.graph.state import GraphState
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately
from app.ai.llm import llm, structured_llm
from app.ai.schema import RouterType

async def llm_node(state: GraphState) -> dict:

    system_prompt = get_system_prompt(
        summary=state.get("summary", ""),
        retrieved_context=state.get("retrieved_context", ""),
        retrieval_found=state.get("retrieval_found", False)
    )

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    res = await llm.ainvoke(messages)

    return {
        "messages": [res],
    }


async def summarisation_node(state: GraphState) -> dict:
    tokensCount = count_tokens_approximately(state["messages"])
    print(tokensCount)
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
        # print("summary",summary_respone.content)
        return {
            "summary": summary_respone.content,
            "last_summarised_msg_id": messges_to_summarise[-1].id,
            "messages": [RemoveMessage(id=msg.id) for msg in messages_to_remove],
        }


async def retreive_context_node(state: GraphState) -> dict:
    query = state["messages"][-1].content

    context, success = await retreive_context(
        query=query, conversation_id=str(state.get("conversation_id", ""))
    )
    print("retrieved context", context, "\n Success: ",success)
    return {
        "retrieved_context": context,
        "retrieval_found": success
    }


async def evaluator_node(state: GraphState) -> dict:
    
    query = state["messages"][-1].content

    response = await structured_llm.ainvoke(
        [
            SystemMessage(content=get_evaluator_prompt()),
            HumanMessage(content=query)
        ]
    )

    print("evaluator Reasoning: ", response.reasoning)
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
    pass