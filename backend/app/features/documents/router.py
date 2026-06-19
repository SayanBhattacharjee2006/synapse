import uuid

from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.model import User
from app.features.documents.schemas import DocumentResponse
from app.features.documents.service import upload_document, get_document, delete_document

router = APIRouter(tags=["documents"])


@router.post(
    "/conversations/{conversation_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_handler(
    conversation_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = await upload_document(
        db=db,
        file=file,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )

    return document

@router.get(
    "/conversations/{conversation_id}/documents",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK
)
async def get_all_documents(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = await get_document(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    return documents

@router.delete(
    "/conversations/{conversation_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_document_route(
    conversation_id:uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_document(
        db=db,
        document_id=document_id,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
