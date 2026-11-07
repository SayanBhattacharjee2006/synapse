from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.features.documents.application.enums import (
    ProcessingStatusEnum,
    UploadStatusEnum,
)


class UploadInitiateRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0)


class UploadInitiateResponse(BaseModel):
    document_id: uuid.UUID
    presigned_url: str
    required_headers: dict[str, str]
    expires_in: int
    s3_key: str


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
    file_size: int
    processing_status: ProcessingStatusEnum
    upload_status: UploadStatusEnum = UploadStatusEnum.completed
    upload_confirmed_at: Optional[datetime] = None

