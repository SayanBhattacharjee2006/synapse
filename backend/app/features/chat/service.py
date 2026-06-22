import uuid
import json
from fastapi import Request
from sqlalchemy import select, update
from app.features.chat.schemas import ChatRequest
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.conversations.models import Message, Conversation
from app.ai.llm import llm
from app.ai.rag.services.summary_memory_sevice import store_summary


async def stream_chat(
    request: Request,
    conversation_id: uuid.UUID,
    message: ChatRequest,
    db: AsyncSession,
    user_id: uuid.UUID,
):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": str(conversation_id)}}

    stmt = (
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False,
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
        )
    )

    messages = (await db.scalars(stmt)).all()

    is_first_message = len(messages) == 1
    summary = None

    async for event in graph.astream_events(
        {
            "messages": [HumanMessage(content=message.content)],
            "conversation_id":str(conversation_id)
        },
        config=config,
        version="v2",
    ):
        if event["event"] == "on_chain_end" and event.get("name") == "summarisation":
            summary = event["data"]["output"].get("summary", "")

        if (
            event["event"] == "on_chat_model_stream"
            and event.get("metadata", {}).get("langgraph_node") == "llm"
        ):
            token = event["data"]["chunk"].content
            if token:
                yield f"data: {token}\n\n"

    update_values = {}

    if summary:
        update_values["summary"] = summary

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
        .where(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False,
            Conversation.user_id == user_id,
        )
        .values(**update_values)
    )
    await db.commit()

    if summary:
        store_summary(summary, conversation_id, user_id)

    if is_first_message:
        yield f"event: title\ndata: {json.dumps({'title': title})}\n\n"

    yield "data: [DONE]\n\n"
