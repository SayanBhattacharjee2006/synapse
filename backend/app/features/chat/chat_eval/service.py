from langchain_core.messages import HumanMessage

from app.features.chat.chat_eval.schema import EvaluationResult


async def run_evaluation(
    question: str,
    conversation_id: str,
    has_uploaded_documents: bool,
    graph,
) -> EvaluationResult:
    config = {
        "configurable": {
            "thread_id": str(conversation_id),
        }
    }

    response = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=question)],
            "conversation_id": str(conversation_id),
            "has_uploaded_documents": has_uploaded_documents,
        },
        config=config,
    )

    return EvaluationResult(
        router=response["router"],
        retrieved_context=response.get("retrieved_context"),
        web_context=response.get("web_context"),
        answer=response["messages"][-1].content,
    )
