import uuid
from fastapi import Request
from app.features.chat.schemas import ChatRequest
from langchain_core.messages import HumanMessage

async def stream_chat(request:Request, conversation_id: uuid.UUID, message: ChatRequest):
    graph= request.app.state.graph
    config={
        "configurable":{
            "thread_id": str(conversation_id)
        }
    }
    async for event in graph.astream_events(
        {"messages": [HumanMessage(content=message.content)]},
        config= config,
        version="v2"
    ):
        if event["event"] == "on_chat_model_stream":
            token = event["data"]["chunk"].content
            if token:
                yield f"data: {token}\n\n"
    yield "data: [DONE]\n\n"