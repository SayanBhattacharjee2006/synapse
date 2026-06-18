import uuid
from pydantic import BaseModel, Field, ConfigDict
from app.features.documents.model import ProcessingStatusEnum

class DocumentResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
    file_size: int
    processing_status : ProcessingStatusEnum 