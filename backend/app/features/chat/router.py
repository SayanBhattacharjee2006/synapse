from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.features.chat import service
from app.features.chat.schemas import ChatRequest
import uuid

router = APIRouter(prefix="/conversations", tags=["chat"])

@router.post("/{conversation_id}/chat", status_code=200)
async def chat(request:Request, conversation_id: uuid.UUID, data: ChatRequest,):
    return StreamingResponse(
        service.stream_chat(request, conversation_id, data),
        media_type="text/event-stream"
    )