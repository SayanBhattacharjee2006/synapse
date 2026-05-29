from pydantic import BaseModel, Field,ConfigDict 
from typing import Optional
import uuid
from datetime import datetime
from app.features.conversations.models import SenderEnum

class ConversationCreate(BaseModel):
    pass

class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    slug: str
    title: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

class MessageCreate(BaseModel):
    content: str
    sender: SenderEnum

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    sender: SenderEnum
    is_deleted: bool
    created_at: datetime
    conversation_id: uuid.UUID
    