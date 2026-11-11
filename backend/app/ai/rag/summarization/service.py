import asyncio
from langchain_core.documents import Document

from app.ai.rag.summarization.grouping import group_by_tokens
from app.ai.rag.summarization.mapper import summarize_group
from app.ai.rag.summarization.reducer import final_reducer, intermediate_reducer
from app.ai.rag.summarization.schemas import IntermediateSummary
from app.contracts.document_profile import DocumentProfile
from app.core.config import settings
from app.core.logging import logger


async def execute_mapper_stage(
    chunks: list[Document],
) -> list[IntermediateSummary]:
    logger.bind(chunk_count=len(chunks)).info("document.summary.mapper.started")
    document_groups = group_by_tokens(
        chunks,
        lambda x: x.page_content,
        threshold=settings.SUMMARY_CHUNK_GROUPING_THRESHOLD,
    )

    summarized_groups = await asyncio.gather(
        *(summarize_group(group) for group in document_groups)
    )

    logger.bind(
        chunk_count=len(chunks),
        group_count=len(document_groups),
    ).info("document.summary.mapper.completed")

    return summarized_groups


async def execute_reducer_stage(
    summary_list: list[IntermediateSummary],
) -> DocumentProfile:
    logger.bind(summary_count=len(summary_list)).info(
        "document.summary.reducer.started"
    )
    while len(summary_list) > 1:
        summarised_groups = group_by_tokens(
            summary_list,
            lambda x: x.summary,
            threshold=settings.INTERMEDIATE_SUMMARY_THRESOLD,
        )
        summary_list = await asyncio.gather(
            *(intermediate_reducer(group) for group in summarised_groups)
        )

    final_summary = await final_reducer(summary_list[0])

    logger.bind().info("document.summary.reducer.completed")

    return final_summary


async def generate_document_profile(chunks: list[Document]) -> DocumentProfile:
    """Pure algorithmic document profile generation from LangChain chunks."""
    intermediate_summaries = await execute_mapper_stage(chunks)
    document_profile = await execute_reducer_stage(intermediate_summaries)
    return document_profile

