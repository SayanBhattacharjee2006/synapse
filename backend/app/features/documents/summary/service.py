import asyncio
from langchain_core.documents import Document
from app.features.documents.summary.schemas import IntermediateSummary
from app.features.documents.summary.mapper import summarize_group

async def summarize_document_groups(document_groups: list[list[Document]]) -> list[IntermediateSummary]:

    summarized_groups = await asyncio.gather(*(summarize_group(group) for group in document_groups))

    return summarized_groups