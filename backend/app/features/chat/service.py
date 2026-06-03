import uuid
from fastapi import Request
from sqlalchemy import select, update
from app.features.chat.schemas import ChatRequest
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.conversations.models import Message, Conversation
from app.ai.llm import llm

async def stream_chat(
    request: Request, conversation_id: uuid.UUID, message: ChatRequest, db: AsyncSession
):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": str(conversation_id)}}

    stmt = select(Message).where(
        Message.conversation_id == conversation_id, Message.is_deleted == False
    )

    messages = (await db.scalars(stmt)).all()

    is_first_message = len(messages) == 1

    async for event in graph.astream_events(
        {"messages": [HumanMessage(content=message.content)]},
        config=config,
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            token = event["data"]["chunk"].content
            if token:
                yield f"data: {token}\n\n"
    yield "data: [DONE]\n\n"

    final_graph_state = await graph.aget_state(config)
    print(final_graph_state.values)
    print("latest_summarised_msg_id",final_graph_state.values.get("last_summarised_msg_id"))
    print("summary",final_graph_state.values.get("summary"))
    print(len(final_graph_state.values["messages"]))
    update_values = {
        "summary": final_graph_state.values.get("summary"),
    }

    if is_first_message:
        title_response = await llm.ainvoke(
            [
                SystemMessage(
                    content="You are a title generator. Generate a short title of maximum 5 words for this conversation. Return only the title, nothing else."
                ),
                HumanMessage(content=message.content),
            ]
        )

        title = title_response.content
        update_values["title"] = title
        update_values["slug"] = title.lower().replace(" ", "-")

    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id, Conversation.is_deleted == False)
        .values(**update_values)
    )
    await db.commit()