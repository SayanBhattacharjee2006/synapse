from app.ai.prompts.chat import SYSTEM_PROMPT
from app.ai.graph.state import GraphState
from langchain_core.messages import SystemMessage
from app.ai.llm import llm

async def llm_node(state:GraphState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state['messages']

    res = await llm.ainvoke(messages)
    return {
        "messages" : [res],
    }