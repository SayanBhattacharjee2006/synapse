import asyncio

from app.features.chat.chat_eval.service import run_evaluation
from app.core.config import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver #
from app.ai.graph.graph import get_graph

from ..evaluators.answer_evaluator.answer_evaluation import answer_evaluation
from ..evaluators.router_evaluator.router_evaluator import router_evaluation
from ..evaluators.retreival_evaluator.retreival_evaluation import retrieval_evaluation


async def evaluation_runner(
    validated_inputs,
    conversation_id,
    has_uploaded_documents,
    validated_outputs,
):
    results = []

    async with AsyncPostgresSaver.from_conn_string(
        str(settings.DATABASE_URL).replace("+asyncpg", "")
    ) as checkpoint_saver:

        await checkpoint_saver.setup()
        graph = get_graph(checkpoint_saver)

        for index, input_data in enumerate(validated_inputs):

            res = await run_evaluation(
                question=input_data["question"],
                conversation_id=conversation_id,
                has_uploaded_documents=has_uploaded_documents,
                graph=graph,
            )

            router_eval_res, answer_eval_res, retrieval_eval_res = await asyncio.gather(
                asyncio.to_thread(
                    router_evaluation,
                    validated_outputs[index]["expected_route"],
                    res.router.value,
                ),

                answer_evaluation(
                    question=input_data["question"],
                    expected_answer=validated_outputs[index]["reference_answer"],
                    generated_answer=res.answer,
                    router=res.router,
                    retrieved_context=res.retrieved_context,
                    web_context=res.web_context,
                ),

                retrieval_evaluation(
                    question=input_data["question"],
                    reference_answer=validated_outputs[index]["reference_answer"],
                    retrieved_context=res.retrieved_context,
                    reference_evidence=validated_outputs[index].get("reference_evidence"),
                )
                if validated_outputs[index]["expected_route"] in ["rag", "both"]
                else asyncio.sleep(0, result=None),
            )

            results.append(
                {
                    "question": input_data["question"],
                    "expected_answer": validated_outputs[index]["reference_answer"],
                    "generated_answer": res.answer,
                    "expected_route": validated_outputs[index]["expected_route"],
                    "predicted_route": res.router.value,
                    "router_evaluation": router_eval_res,
                    "answer_evaluation": answer_eval_res,
                    "retrieval_evaluation": retrieval_eval_res,
                }
            )

    return results