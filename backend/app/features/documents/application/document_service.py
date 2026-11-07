import uuid
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger
from app.features.documents.application.enums import (
    ProcessingStatusEnum,
    UploadStatusEnum,
)
from app.features.documents.application.exceptions import (
    ConversationAccessError,
    DocumentNotFoundError,
    DocumentUploadInvalidError,
    ObjectNotFoundError,
)
from app.features.documents.application.interfaces.conversation_operations import (
    ConversationOperations,
)
from app.features.documents.application.interfaces.document_knowledge_pipeline import (
    DocumentKnowledgePipeline,
)
from app.features.documents.application.interfaces.object_storage import (
    ObjectStorage,
)
from app.features.documents.application.interfaces.unit_of_work import (
    DocumentUnitOfWork,
)
from app.features.documents.infrastructure.persistence.models import Document
from app.integretions.s3.constants import ALLOWED_EXTENSIONS


class DocumentService:

    def __init__(
        self,
        uow: DocumentUnitOfWork,
        storage: ObjectStorage,
        conversation_ops: ConversationOperations,
        knowledge_pipeline: DocumentKnowledgePipeline,
    ) -> None:
        self._uow = uow
        self._storage = storage
        self._conversation_ops = conversation_ops
        self._knowledge_pipeline = knowledge_pipeline

    async def initiate_upload(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        content_type: str,
        file_size: int,
    ) -> dict:
        logger.bind(
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            filename=filename,
            file_size=file_size,
        ).info("document.upload_initiate.started")

        # 1. Validate conversation ownership
        await self._conversation_ops.validate_ownership(
            conversation_id, user_id
        )

        # 2. Validate filename and extension
        if not filename or "." not in filename:
            raise DocumentUploadInvalidError("Valid filename with extension is required")

        ext = filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise DocumentUploadInvalidError(
                f"Invalid file extension '.{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 3. Validate content type
        if not content_type:
            raise DocumentUploadInvalidError("Content-Type is required")

        # 4. Validate file size
        if file_size <= 0:
            raise DocumentUploadInvalidError("File size must be greater than 0")

        if file_size > settings.MAX_FILE_SIZE:
            raise DocumentUploadInvalidError(
                f"File size {file_size} exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
            )

        # 5. Generate document ID and controlled S3 key
        document_id = uuid.uuid4()
        s3_key = f"documents/{user_id}/{conversation_id}/{document_id}/{filename}"

        # 6. Create document record with pending status
        document = Document(
            id=document_id,
            user_id=user_id,
            conversation_id=conversation_id,
            filename=filename,
            mime_type=content_type,
            file_size=file_size,
            s3_key=s3_key,
            upload_status=UploadStatusEnum.pending,
            processing_status=ProcessingStatusEnum.pending,
        )

        await self._uow.documents.create(document)
        await self._uow.commit()

        # 7. Generate presigned PUT URL
        presigned_url = await self._storage.generate_presigned_upload_url(
            key=s3_key,
            content_type=content_type,
            expires_in=900,
        )

        logger.bind(
            document_id=str(document_id),
            s3_key=s3_key,
        ).info("document.upload_initiate.completed")

        return {
            "document_id": document_id,
            "presigned_url": presigned_url,
            "required_headers": {"Content-Type": content_type},
            "expires_in": 900,
            "s3_key": s3_key,
        }

    async def confirm_upload(
        self,
        conversation_id: uuid.UUID,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Document:
        logger.bind(
            conversation_id=str(conversation_id),
            document_id=str(document_id),
            user_id=str(user_id),
        ).info("document.upload_confirm.started")

        document = await self._uow.documents.get_by_id_and_owner(
            document_id, conversation_id, user_id
        )
        if document is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")

        # Idempotency: if already confirmed, return existing document
        if document.upload_status == UploadStatusEnum.completed:
            return document

        # Verify object exists in S3
        try:
            metadata = await self._storage.get_object_metadata(document.s3_key)
        except ObjectNotFoundError as e:
            raise DocumentUploadInvalidError(
                f"S3 object '{document.s3_key}' not found. Direct upload to S3 must be completed first."
            ) from e

        actual_size = metadata.get("size", 0)
        if actual_size <= 0:
            raise DocumentUploadInvalidError("Uploaded file in S3 is empty")

        if actual_size > settings.MAX_FILE_SIZE:
            raise DocumentUploadInvalidError(
                f"Uploaded file size ({actual_size}) exceeds maximum allowed limit"
            )

        # Update document state
        document.upload_status = UploadStatusEnum.completed
        document.upload_confirmed_at = datetime.now(timezone.utc)
        document.file_size = actual_size
        if metadata.get("content_type"):
            document.mime_type = metadata["content_type"]

        # Adjust conversation document count
        await self._conversation_ops.adjust_document_count(
            conversation_id, user_id, delta=1
        )

        await self._uow.commit()
        await self._uow.refresh(document)

        logger.bind(
            document_id=str(document_id),
            actual_size=actual_size,
        ).info("document.upload_confirm.completed")

        return document

    async def get_document(
        self,
        conversation_id: uuid.UUID,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Document:
        await self._conversation_ops.validate_ownership(
            conversation_id, user_id
        )

        document = await self._uow.documents.get_by_id_and_owner(
            document_id, conversation_id, user_id
        )
        if document is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")

        return document

    async def list_documents(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[Document]:
        await self._conversation_ops.validate_ownership(
            conversation_id, user_id
        )

        return await self._uow.documents.list_by_conversation(
            conversation_id, user_id
        )

    async def delete_document(
        self,
        conversation_id: uuid.UUID,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        logger.bind(
            conversation_id=str(conversation_id),
            document_id=str(document_id),
            user_id=str(user_id),
        ).info("document.delete.started")

        document = await self._uow.documents.get_by_id_and_owner(
            document_id, conversation_id, user_id, include_soft_deleted=True
        )
        if document is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")

        # 1. Prevent new processing by setting is_deleted = True
        if not document.is_deleted:
            await self._uow.documents.mark_deletion_started(document_id)
            await self._uow.commit()

        # 2. Delete indexed knowledge from Qdrant
        await self._knowledge_pipeline.delete_document_knowledge(document_id)

        # 3. Delete file object from S3
        await self._storage.delete_object(document.s3_key)

        # 4. Decrement conversation document count if it was previously confirmed
        if document.upload_status == UploadStatusEnum.completed:
            try:
                await self._conversation_ops.adjust_document_count(
                    conversation_id, user_id, delta=-1
                )
            except Exception:
                logger.bind(document_id=str(document_id)).warning(
                    "document.delete.adjust_count_failed"
                )

        # 5. Physical deletion of PostgreSQL document record
        await self._uow.documents.hard_delete(document_id)
        await self._uow.commit()

        logger.bind(document_id=str(document_id)).info(
            "document.delete.completed"
        )

