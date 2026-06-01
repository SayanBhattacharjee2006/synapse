from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from app.features.chat import service
from app.features.chat.schemas import ChatRequest
from app.core.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

router = APIRouter(prefix="/conversations", tags=["chat"])

@router.post("/{conversation_id}/chat", status_code=200)
async def chat(request:Request, conversation_id: uuid.UUID, data: ChatRequest,db: AsyncSession = Depends(get_db)):
    return StreamingResponse(
        service.stream_chat(request, conversation_id, data, db),
        media_type="text/event-stream"
    )