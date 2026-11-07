import asyncio
import os
from pathlib import Path
import tempfile
from typing import Callable
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.features.documents.application.enums import ProcessingStatusEnum
from app.features.documents.application.interfaces.document_knowledge_pipeline import (
    DocumentKnowledgePipeline,
)
from app.features.documents.application.interfaces.object_storage import (
    ObjectStorage,
)
from app.features.documents.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyDocumentUnitOfWork,
)


class DocumentProcessingService:

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        storage: ObjectStorage,
        knowledge_pipeline: DocumentKnowledgePipeline,
        max_concurrency: int = 3,
    ) -> None:
        self._session_factory = session_factory
        self._storage = storage
        self._knowledge_pipeline = knowledge_pipeline
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def process_document_by_id(self, document_id: uuid.UUID) -> None:
        """Process document using an independent database session with concurrency limiting."""
        async with self._semaphore:
            await self._execute_processing(document_id)

    async def _execute_processing(self, document_id: uuid.UUID) -> None:
        temp_file_path: str | None = None

        # 1. Claim document for processing using an independent session
        async with self._session_factory() as session:
            uow = SQLAlchemyDocumentUnitOfWork(session)
            document = await uow.documents.claim_for_processing(document_id)
            if document is None:
                logger.bind(document_id=str(document_id)).info(
                    "document.processing.claim_skipped_or_already_active"
                )
                return
            await uow.commit()

            # Capture needed fields for processing
            conversation_id = document.conversation_id
            user_id = document.user_id
            filename = document.filename
            s3_key = document.s3_key

        logger.bind(
            document_id=str(document_id),
            filename=filename,
        ).info("document.processing.started")

        # 2. Execute download and knowledge pipeline
        try:
            # Check deletion boundary before heavy processing
            async with self._session_factory() as session:
                uow = SQLAlchemyDocumentUnitOfWork(session)
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

            # Delegate knowledge indexing and summarization to AI/RAG adapter
            await self._knowledge_pipeline.process_document_knowledge(
                document_id=document_id,
                conversation_id=conversation_id,
                user_id=user_id,
                filename=filename,
                file_path=temp_file_path,
            )

            # 3. Final state update: Completed
            async with self._session_factory() as session:
                uow = SQLAlchemyDocumentUnitOfWork(session)
                current = await uow.documents.get_by_id(document_id)
                if current is not None and not current.is_deleted:
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
            # Update failed status in database
            try:
                async with self._session_factory() as session:
                    uow = SQLAlchemyDocumentUnitOfWork(session)
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

