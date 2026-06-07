import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.features.conversations import service
from app.features.conversations.schemas import (
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
    MessageCreate,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.model import User

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/", response_model=list[ConversationResponse])
async def get_conversations(db: AsyncSession = Depends(get_db),current_user : User = Depends(get_current_user)):
    return await service.get_all_conversations(db,current_user.id)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_by_id(
    conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db),current_user : User = Depends(get_current_user)
):
    try:
        return await service.get_conversation_by_id(db, conversation_id,current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ConversationResponse, status_code=201)
async def conversation_create(db: AsyncSession = Depends(get_db),current_user : User = Depends(get_current_user)):
    return await service.create_conversations(db,current_user.id)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def conversation_update(
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user),
):
    try:
        return await service.update_conversations(db, conversation_id, data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{conversation_id}", status_code=204)
async def conversation_delete(
    conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user : User = Depends(get_current_user)
):
    try:
        await service.delete_conversation(db, conversation_id, current_user.id)
        return
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



# Messages Routes

@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user : User = Depends(get_current_user)):
    return await service.get_messages(db, conversation_id, current_user.id)


@router.post(
    "/{conversation_id}/messages", response_model=MessageResponse, status_code=201
)
async def message_create(
    conversation_id: uuid.UUID, data: MessageCreate, db: AsyncSession = Depends(get_db), current_user : User = Depends(get_current_user)
):
    return await service.create_message(db, conversation_id, data, current_user.id)


@router.delete("/{conversation_id}/messages/{message_id}", status_code=204)
async def message_delete(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user),
):
    try:
        await service.delete_message(db, message_id, conversation_id, current_user.id)
        return
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
