import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.features.conversations import service
from app.features.conversations.schemas import ConversationResponse, ConversationUpdate, MessageResponse,MessageCreate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("/", response_model=list[ConversationResponse])
async def get_conversations(db: AsyncSession = Depends(get_db)):
    return await service.get_all_conversations(db)

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_by_id(conversation_id: uuid.UUID,db: AsyncSession = Depends(get_db)):
    try:
        return await service.get_conversation_by_id(db, conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/", response_model=ConversationResponse, status_code=201)
async def conversation_create(db: AsyncSession = Depends(get_db)):
    return await service.create_conversations(db)

@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def conversation_update(conversation_id: uuid.UUID, data: ConversationUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.update_conversations(db, conversation_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{conversation_id}", status_code=204)
async def conversation_delete(conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await service.delete_conversation(db, conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(conversation_id: uuid.UUID,db: AsyncSession = Depends(get_db)):
    return await service.get_messages(db, conversation_id)

@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def message_create(conversation_id: uuid.UUID, data: MessageCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_message(db, conversation_id, data)

@router.delete("/{conversation_id}/messages/{message_id}", status_code=204)
async def message_delete(conversation_id: uuid.UUID, message_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await service.delete_message(db, message_id, conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))










# GET    /{conversation_id}/messages
# POST   /{conversation_id}/messages
# DELETE /{conversation_id}/messages/{message_id}