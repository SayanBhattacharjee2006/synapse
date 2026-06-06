from app.ai.prompts.chat import get_summariser_prompt,get_system_prompt
from app.ai.graph.state import GraphState
from langchain_core.messages import SystemMessage, RemoveMessage
from langchain_core.messages.utils import count_tokens_approximately
from app.ai.llm import llm

async def llm_node(state:GraphState) -> dict:
    messages = [SystemMessage(content=get_system_prompt(state.get("summary", "")))] + state['messages']
    res = await llm.ainvoke(messages)
    return {
        "messages" : [res],
    }


async def summarisation_node(state: GraphState) -> dict:
    tokensCount = count_tokens_approximately(state['messages'])
    print(tokensCount)
    if tokensCount < 2500:
        return {}
    else:
        if state.get("last_summarised_msg_id","") is None:
            last_summarised_msg_idx = 0
        else:
            last_summarised_msg_idx = next(
                (
                    idx
                    for idx, msg in enumerate(state["messages"])
                    if msg.id == state.get("last_summarised_msg_id","")
                ),
                None,
            )

        if last_summarised_msg_idx is None:
            last_summarised_msg_idx = 0

        messges_to_summarise = state["messages"][last_summarised_msg_idx+1:len(state["messages"])-10]

        if not messges_to_summarise:
            return {}

        summary_respone = await llm.ainvoke([SystemMessage(content=get_summariser_prompt(state.get("summary", ""), messges_to_summarise))])
        messages_to_remove = state["messages"][:-10]
        # print("summary",summary_respone.content)
        return {
            "summary": summary_respone.content,
            "last_summarised_msg_id": messges_to_summarise[-1].id,
            "messages": [RemoveMessage(id=msg.id) for msg in messages_to_remove],
        }

        