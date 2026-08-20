from .prompt import get_retrieval_eval_prompt
from .schema import RetrievalEvalSchema
from app.ai.llm import llm


async def retrieval_evaluation(
    question: str,
    reference_answer: str,
    retrieved_context: str | None,
    reference_evidence: dict | None,
) -> RetrievalEvalSchema:

    prompt = get_retrieval_eval_prompt(
        question=question,
        reference_answer=reference_answer,
        retrieved_context=retrieved_context,
        reference_evidence=reference_evidence,
    )

    retrieval_eval_llm = llm.with_structured_output(
        RetrievalEvalSchema
    )

    response = await retrieval_eval_llm.ainvoke(prompt)

    return response