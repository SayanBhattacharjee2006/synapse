import asyncio
from app.features.chat.chat_eval.schema import EvaluationResult
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import settings
from app.ai.graph.graph import get_graph

async def run_evaluation(
    question: str,
    conversation_id: str,
    has_uploaded_documents: bool,
    graph
) -> EvaluationResult:
    
    config = {
        "configurable": {
            "thread_id": str(conversation_id),
        }
    }

    response = await graph.ainvoke(
        {
            "messages" : [HumanMessage(content=question)],
            "conversation_id": str(conversation_id),
            "has_uploaded_documents": has_uploaded_documents
        },
        config=config,
    )

    return EvaluationResult(
        router = response["router"],
        retrieved_context = response.get("retrieved_context"),
        web_context = response.get("web_context"),
        answer = response["messages"][-1].content
    )


# async def test_runner():
    # async with AsyncPostgresSaver.from_conn_string(str(settings.DATABASE_URL).replace("+asyncpg", "")) as checkpoint_saver:
    #     await checkpoint_saver.setup()
    #     graph = get_graph(checkpoint_saver)

    #     res = await run_evaluation(
    #         question="What is 15% of 240?",
    #         conversation_id="ef302fd8-7a44-40a7-b9f6-bdd89f743ede",
    #         has_uploaded_documents=True,
    #         graph=graph,
    #     )

    #     print("Result: ", res)


# if __name__ == "__main__":
#     asyncio.run(test_runner())