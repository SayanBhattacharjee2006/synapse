import uuid
from datetime import datetime, timezone
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.documents.application.enums import (
    ProcessingStatusEnum,
    UploadStatusEnum,
)
from app.features.documents.application.interfaces.document_repository import (
    DocumentRepository,
)
from app.features.documents.infrastructure.persistence.models import Document


class SQLAlchemyDocumentRepository(DocumentRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, document: Document) -> Document:
        self._session.add(document)
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.is_deleted == False,
        )
        return (await self._session.scalars(stmt)).one_or_none()

    async def get_by_id_and_owner(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        include_soft_deleted: bool = False,
    ) -> Document | None:
        conditions = [
            Document.id == document_id,
            Document.conversation_id == conversation_id,
            Document.user_id == user_id,
        ]
        if not include_soft_deleted:
            conditions.append(Document.is_deleted == False)

        stmt = select(Document).where(*conditions)
        return (await self._session.scalars(stmt)).one_or_none()

    async def list_by_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Document]:
        stmt = (
            select(Document)
            .where(
                Document.conversation_id == conversation_id,
                Document.user_id == user_id,
                Document.is_deleted == False,
                Document.upload_status == UploadStatusEnum.completed,
            )
            .order_by(Document.created_at.desc())
        )
        return list((await self._session.scalars(stmt)).all())

    async def count_by_conversation(self, conversation_id: uuid.UUID) -> int:
        stmt = (
            select(func.count(Document.id))
            .where(
                Document.conversation_id == conversation_id,
                Document.is_deleted == False,
                Document.upload_status == UploadStatusEnum.completed,
            )
        )
        result = await self._session.scalar(stmt)
        return int(result or 0)

    async def claim_for_processing(
        self, document_id: uuid.UUID
    ) -> Document | None:
        stmt = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.upload_status == UploadStatusEnum.completed,
                Document.processing_status == ProcessingStatusEnum.pending,
                Document.is_deleted == False,
            )
            .with_for_update()
        )
        document = (await self._session.scalars(stmt)).one_or_none()
        if document is not None:
            document.processing_status = ProcessingStatusEnum.processing
        return document

    async def update_processing_status(
        self,
        document_id: uuid.UUID,
        status: ProcessingStatusEnum,
        error_message: str | None = None,
    ) -> None:
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(
                processing_status=status,
                error_message=error_message,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._session.execute(stmt)

    async def update_upload_status(
        self,
        document_id: uuid.UUID,
        status: UploadStatusEnum,
        confirmed_at: datetime | None = None,
    ) -> None:
        values = {"upload_status": status, "updated_at": datetime.now(timezone.utc)}
        if confirmed_at is not None:
            values["upload_confirmed_at"] = confirmed_at

        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(**values)
        )
        await self._session.execute(stmt)

    async def mark_deletion_started(self, document_id: uuid.UUID) -> None:
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(
                is_deleted=True,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._session.execute(stmt)

    async def hard_delete(self, document_id: uuid.UUID) -> None:
        stmt = delete(Document).where(Document.id == document_id)
        await self._session.execute(stmt)

