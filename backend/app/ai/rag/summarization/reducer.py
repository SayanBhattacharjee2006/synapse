from app.ai.llm import (
    final_reducer_llm,
    intermediate_reducer_llm,
)
from app.ai.rag.summarization.formatter import summary_serializer
from app.ai.rag.summarization.prompts import (
    get_final_reducer_prompt,
    get_intermediate_reducer_prompt,
)
from app.ai.rag.summarization.schemas import IntermediateSummary
from app.contracts.document_profile import DocumentProfile
from app.core.logging import logger


async def intermediate_reducer(
    intermediate_summaries: list[IntermediateSummary],
) -> IntermediateSummary:
    logger.bind(
        summary_count=len(intermediate_summaries),
    ).info("document.summary.intermediate_reducer.started")
    combined_summary = summary_serializer(intermediate_summaries)

    prompt = get_intermediate_reducer_prompt(combined_summary)
    response = await intermediate_reducer_llm.ainvoke(prompt)

    logger.bind(
        summary_count=len(intermediate_summaries),
    ).info("document.summary.intermediate_reducer.completed")

    return response


async def final_reducer(
    intermediate_summary: IntermediateSummary,
) -> DocumentProfile:
    logger.bind().info("document.summary.final_reducer.started")

    serialized_summary = summary_serializer([intermediate_summary])
    prompt = get_final_reducer_prompt(serialized_summary)
    response = await final_reducer_llm.ainvoke(prompt)

    logger.bind().info("document.summary.final_reducer.completed")

    return response

