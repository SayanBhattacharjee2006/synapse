import asyncio
from langchain_core.documents import Document
from app.features.documents.summary.schemas import IntermediateSummary
from app.features.documents.summary.mapper import summarize_group
from app.features.documents.summary.reducer import intermediate_reducer, final_reducer
from app.features.documents.summary.schemas import DocumentProfile
from app.features.documents.summary.grouping import group_by_tokens
from app.core.config import settings

async def execute_mapper_stage(chunks: list[Document]) -> list[IntermediateSummary]:
    document_groups = group_by_tokens(chunks, lambda x: x.page_content, threshold=settings.SUMMARY_CHUNK_GROUPING_THRESHOLD)

    summarized_groups = await asyncio.gather(*(summarize_group(group) for group in document_groups))

    return summarized_groups


async def execute_reducer_stage(summary_list: list[IntermediateSummary]) -> DocumentProfile:
    while len(summary_list) > 1:
        summarised_groups = group_by_tokens(summary_list, lambda x: x.summary, threshold=settings.INTERMEDIATE_SUMMARY_THRESOLD)
        summary_list = await asyncio.gather(*(intermediate_reducer(group) for group in summarised_groups))

    final_summary = await final_reducer(summary_list[0])

    return final_summary

async def generate_document_profile(chunks: list[Document]) -> DocumentProfile:
    intermediate_summaries = await execute_mapper_stage(chunks)
    document_profile = await execute_reducer_stage(intermediate_summaries)
    return document_profile