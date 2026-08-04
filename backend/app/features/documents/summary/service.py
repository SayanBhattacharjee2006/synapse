import asyncio
import uuid
from langchain_core.documents import Document
from datetime import datetime, timezone
from app.features.documents.summary.schemas import IntermediateSummary, DocumentProfile
from app.features.documents.summary.mapper import summarize_group
from app.features.documents.summary.reducer import intermediate_reducer, final_reducer
from app.features.documents.summary.grouping import group_by_tokens
from app.features.documents.service import (
    update_document_profile,
    update_doc_summary_status,
    get_document,
)
from app.ai.rag.services.document_summary_service import store_document_summary
from app.features.documents.model import ProcessingStatusEnum
from app.core.config import settings
from app.core.database import session_factory


async def execute_mapper_stage(chunks: list[Document]) -> list[IntermediateSummary]:
    document_groups = group_by_tokens(
        chunks,
        lambda x: x.page_content,
        threshold=settings.SUMMARY_CHUNK_GROUPING_THRESHOLD,
    )

    summarized_groups = await asyncio.gather(
        *(summarize_group(group) for group in document_groups)
    )

    return summarized_groups


async def execute_reducer_stage(
    summary_list: list[IntermediateSummary],
) -> DocumentProfile:
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

    return final_summary


async def generate_document_profile(chunks: list[Document]) -> DocumentProfile:
    intermediate_summaries = await execute_mapper_stage(chunks)
    document_profile = await execute_reducer_stage(intermediate_summaries)
    return document_profile


async def execute_doc_summary_pipeline(
    chunks: list[Document],
    document_id: uuid.UUID,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
):
    async with session_factory() as session:
        try:
            doc = await get_document(
                session,
                conversation_id,
                user_id,
                document_id,
            )

            await update_doc_summary_status(
                doc,
                status=ProcessingStatusEnum.processing,
            )

            document_profile = await generate_document_profile(chunks)

            await update_document_profile(
                doc,
                document_profile,
            )

            await store_document_summary(
                doc,
                document_profile,
            )

            await update_doc_summary_status(
                doc,
                status=ProcessingStatusEnum.completed,
                generated_time=datetime.now(timezone.utc),
            )

            await session.commit()

        except Exception:
            await session.rollback()

            try:
                async with session_factory() as failure_session:
                    doc = await get_document(
                        failure_session,
                        conversation_id,
                        user_id,
                        document_id,
                    )

                    await update_doc_summary_status(
                        doc,
                        status=ProcessingStatusEnum.failed,
                    )

                    await failure_session.commit()

            except Exception:
                pass

            raise
