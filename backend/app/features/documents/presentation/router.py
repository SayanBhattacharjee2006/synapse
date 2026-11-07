import uuid
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)

from app.features.auth.dependencies import get_current_user
from app.features.auth.model import User
from app.features.documents.application.document_processing_service import (
    DocumentProcessingService,
)
from app.features.documents.application.document_service import (
    DocumentService,
)
from app.features.documents.application.exceptions import (
    ConversationAccessError,
    DocumentNotFoundError,
    DocumentUploadInvalidError,
)
from app.features.documents.presentation.schemas import (
    DocumentResponse,
    UploadInitiateRequest,
    UploadInitiateResponse,
)
from app.features.documents.wiring import (
    get_document_processing_service,
    get_document_service,
)

router = APIRouter(tags=["documents"])


# ------------------------------------------------------------------------------
# Presigned Upload Endpoints
# ------------------------------------------------------------------------------


@router.post(
    "/conversations/{conversation_id}/documents/upload-init",
    response_model=UploadInitiateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_upload_endpoint(
    conversation_id: uuid.UUID,
    data: UploadInitiateRequest,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        result = await document_service.initiate_upload(
            conversation_id=conversation_id,
            user_id=current_user.id,
            filename=data.filename,
            content_type=data.content_type,
            file_size=data.file_size,
        )
        return result
    except ConversationAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except DocumentUploadInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post(
    "/conversations/{conversation_id}/documents/{document_id}/upload-confirm",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_upload_endpoint(
    conversation_id: uuid.UUID,
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
    processing_service: DocumentProcessingService = Depends(
        get_document_processing_service
    ),
):
    try:
        document = await document_service.confirm_upload(
            conversation_id=conversation_id,
            document_id=document_id,
            user_id=current_user.id,
        )

        # Trigger background processing task using document ID
        background_tasks.add_task(
            processing_service.process_document_by_id, document.id
        )

        return document
    except ConversationAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except DocumentUploadInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


# ------------------------------------------------------------------------------
# Document Management Endpoints
# ------------------------------------------------------------------------------


@router.get(
    "/conversations/{conversation_id}/documents",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_documents(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        return await document_service.list_documents(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
    except ConversationAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get(
    "/conversations/{conversation_id}/documents/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document_by_id_endpoint(
    conversation_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        return await document_service.get_document(
            conversation_id=conversation_id,
            document_id=document_id,
            user_id=current_user.id,
        )
    except ConversationAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete(
    "/conversations/{conversation_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document_route(
    conversation_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        await document_service.delete_document(
            conversation_id=conversation_id,
            document_id=document_id,
            user_id=current_user.id,
        )
        return
    except ConversationAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
