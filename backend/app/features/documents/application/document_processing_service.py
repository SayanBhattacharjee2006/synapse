import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from typing import Callable
import uuid

from app.core.logging import logger
from app.features.documents.application.enums import ProcessingStatusEnum
from app.features.documents.application.interfaces.document_knowledge_pipeline import (
    DocumentKnowledgePipeline,
)
from app.features.documents.application.interfaces.object_storage import (
    ObjectStorage,
)
from app.features.documents.application.interfaces.unit_of_work import (
    DocumentUnitOfWork,
)


class DocumentProcessingService:

    def __init__(
        self,
        uow_factory: Callable[[], DocumentUnitOfWork],
        storage: ObjectStorage,
        knowledge_pipeline: DocumentKnowledgePipeline,
        semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._storage = storage
        self._knowledge_pipeline = knowledge_pipeline
        self._semaphore = semaphore or asyncio.Semaphore(3)

    async def process_document_by_id(self, document_id: uuid.UUID) -> None:
        """Process document using an independent database session with concurrency limiting."""
        async with self._semaphore:
            await self._execute_processing(document_id)

    async def _execute_processing(self, document_id: uuid.UUID) -> None:
        temp_file_path: str | None = None

        # 1. Claim document for processing using an independent Unit of Work
        async with self._uow_factory() as uow:
            document = await uow.documents.claim_for_processing(document_id)
            if document is None:
                logger.bind(document_id=str(document_id)).info(
                    "document.processing.claim_skipped_or_already_active"
                )
                return
            conversation_id = document.conversation_id
            user_id = document.user_id
            filename = document.filename
            s3_key = document.s3_key
            await uow.commit()

        logger.bind(
            document_id=str(document_id),
            filename=filename,
        ).info("document.processing.started")

        # 2. Execute download and knowledge pipeline
        try:
            # Check deletion boundary before expensive operations
            async with self._uow_factory() as uow:
                current = await uow.documents.get_by_id(document_id)
                if current is None or current.is_deleted:
                    logger.bind(document_id=str(document_id)).warning(
                        "document.processing.aborted_due_to_deletion"
                    )
                    return

            # Download S3 object to local temporary file
            suffix = Path(filename).suffix or ".tmp"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                temp_file_path = tmp.name

            await self._storage.download_file(s3_key, temp_file_path)

            # Delegate knowledge indexing and algorithmic summarization to adapter
            doc_profile = (
                await self._knowledge_pipeline.process_document_knowledge(
                    document_id=document_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    filename=filename,
                    file_path=temp_file_path,
                )
            )

            # 3. Post-processing deletion race check
            async with self._uow_factory() as uow:
                current = await uow.documents.get_by_id(
                    document_id, include_soft_deleted=True
                )
                if current is None or current.is_deleted:
                    logger.bind(document_id=str(document_id)).warning(
                        "document.processing.race_detected_cleaning_up"
                    )
                    # Clean up vectors that were indexed during race
                    await self._knowledge_pipeline.delete_document_knowledge(
                        document_id
                    )
                    return

                # Persist summary profile and mark completed
                await uow.documents.update_document_summary(
                    document_id=document_id,
                    summary=doc_profile.summary if doc_profile else None,
                    topics=doc_profile.topics if doc_profile else None,
                    summary_status=ProcessingStatusEnum.completed,
                    generated_at=datetime.now(timezone.utc),
                )
                await uow.documents.update_processing_status(
                    document_id,
                    status=ProcessingStatusEnum.completed,
                    error_message=None,
                )
                await uow.commit()

            logger.bind(document_id=str(document_id)).info(
                "document.processing.completed"
            )

        except Exception as e:
            logger.bind(document_id=str(document_id)).exception(
                "document.processing.failed"
            )
            try:
                async with self._uow_factory() as uow:
                    current = await uow.documents.get_by_id(
                        document_id, include_soft_deleted=True
                    )
                    if current is not None and not current.is_deleted:
                        await uow.documents.update_processing_status(
                            document_id,
                            status=ProcessingStatusEnum.failed,
                            error_message=str(e),
                        )
                        await uow.commit()
            except Exception:
                logger.bind(document_id=str(document_id)).warning(
                    "document.processing.status_update_failed"
                )

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass
