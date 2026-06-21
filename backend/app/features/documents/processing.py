import uuid
import os
from app.core.database import session_factory
from app.features.documents.model import Document, ProcessingStatusEnum
from sqlalchemy import select
from app.integretions.s3.service import download_from_s3
from app.ai.rag.ingestion.ingest import ingest_document


async def process_document(document_id: uuid.UUID):
    async with session_factory() as session:
        document = None
        file_path = None
        try:
            stmt = select(Document).where(
                Document.id == document_id,
                Document.is_deleted == False
            )

            document = (await session.scalars(stmt)).one_or_none()

            if document is None:
                raise ValueError("Document not found")

            document.processing_status = ProcessingStatusEnum.processing

            await session.commit()

            s3_key = document.s3_key

            file_path = download_from_s3(s3_key)

            await ingest_document(document, file_path)

            document.processing_status = ProcessingStatusEnum.completed
            document.error_message = None
            await session.commit() 

            print(f"Document processing completed: {document.filename}")

        except Exception as e:
            if document :
                document.processing_status = ProcessingStatusEnum.failed
                document.error_message = str(e)
                await session.commit()
            print(f"Document processing failed: {e}")

        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            