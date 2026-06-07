from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from app.features.chat import service
from app.features.chat.schemas import ChatRequest
from app.core.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.dependencies import get_current_user
from app.features.auth.model import User
import uuid

router = APIRouter(prefix="/conversations", tags=["chat"])


@router.post("/{conversation_id}/chat", status_code=200)
async def chat(
    request: Request,
    conversation_id: uuid.UUID,
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user),
):
    return StreamingResponse(
        service.stream_chat(request, conversation_id, data, db, current_user.id),
        media_type="text/event-stream",
    )
