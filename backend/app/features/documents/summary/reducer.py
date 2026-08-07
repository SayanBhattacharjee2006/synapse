from app.features.documents.summary.schemas import IntermediateSummary
from app.features.documents.formatter import summary_serializer
from app.ai.llm import (
    mapper_llm,
    intermediate_reducer_llm,
    final_reducer_llm,
)  # because it uses IntermediateSummary as the structured output
from app.features.documents.summary.prompts import (
    get_intermediate_reducer_prompt,
    get_final_reducer_prompt,
)
from app.features.documents.summary.schemas import DocumentProfile
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


async def final_reducer(intermediate_summary: IntermediateSummary) -> DocumentProfile:
    logger.bind().info("document.summary.final_reducer.started")

    serialized_summary = summary_serializer([intermediate_summary])

    prompt = get_final_reducer_prompt(serialized_summary)

    response = await final_reducer_llm.ainvoke(prompt)

    logger.bind().info("document.summary.final_reducer.completed")

    return response
