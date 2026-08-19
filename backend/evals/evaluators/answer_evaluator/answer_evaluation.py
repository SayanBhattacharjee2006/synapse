from .prompt import get_answer_eval_prompt
from .schema import AnswerEvalSchema
from app.ai.llm import llm

async def answer_evaluation(
    question,
    expected_answer,
    generated_answer,
    router,
    retrieved_context,
    web_context,
):
    prompt = get_answer_eval_prompt(
        question=question,
        expected_answer=expected_answer,
        answer=generated_answer,
        router=router,
        retrieved_context=retrieved_context,
        web_context=web_context,
    )

    answer_eval_llm = llm.with_structured_output(AnswerEvalSchema)

    response = await answer_eval_llm.ainvoke(prompt)

    return response