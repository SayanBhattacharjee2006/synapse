import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.features.auth.dependencies import get_current_user
from app.features.auth.model import User
from app.features.chat.application.chat_service import ChatService
from app.features.chat.application.exceptions import ConversationNotFoundError
from app.features.chat.presentation.schemas import ChatRequest
from app.features.chat.presentation.streaming import format_sse_stream
from app.features.chat.wiring import get_chat_service

router = APIRouter(prefix="/conversations", tags=["chat"])


@router.post("/{conversation_id}/chat", status_code=status.HTTP_200_OK)
async def chat(
    request: Request,
    conversation_id: uuid.UUID,
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    # Validate conversation access before returning StreamingResponse.
    # Nonexistent or inaccessible conversations must return HTTP 404 directly.
    try:
        await chat_service.validate_access(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    # Begin streaming only after successful authorization
    event_stream = chat_service.stream_chat(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=data.content,
    )

    return StreamingResponse(
        format_sse_stream(event_stream),
        media_type="text/event-stream",
    )

