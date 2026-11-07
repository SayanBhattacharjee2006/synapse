import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from app.features.auth.dependencies import get_current_user
from app.features.auth.model import User
from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.application.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
)
from app.features.conversations.application.message_service import (
    MessageService,
)
from app.features.conversations.presentation.schemas import (
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.features.conversations.wiring import (
    get_conversation_service,
    get_message_service,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ------------------------------------------------------------------------------
# Conversation Routes
# ------------------------------------------------------------------------------


@router.get("/", response_model=list[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    return await conversation_service.list_conversations(current_user.id)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_by_id(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    try:
        return await conversation_service.get_conversation(
            conversation_id, current_user.id
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def conversation_create(
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    return await conversation_service.create_conversation(current_user.id)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def conversation_update(
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    try:
        return await conversation_service.update_conversation(
            conversation_id, current_user.id, data
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def conversation_delete(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    try:
        await conversation_service.delete_conversation(
            conversation_id, current_user.id
        )
        return
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


# ------------------------------------------------------------------------------
# Message Routes
# ------------------------------------------------------------------------------


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
):
    try:
        return await message_service.get_messages(
            conversation_id, current_user.id
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def message_create(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
):
    try:
        return await message_service.create_message(
            conversation_id, current_user.id, data
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete(
    "/{conversation_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def message_delete(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
):
    try:
        await message_service.delete_message(
            message_id, conversation_id, current_user.id
        )
        return
    except (ConversationNotFoundError, MessageNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )

