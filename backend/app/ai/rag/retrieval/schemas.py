from uuid import UUID
from pydantic import BaseModel


class DocumentSummarySchema(BaseModel):
    document_id: UUID
    conversation_id: str
    user_id: UUID
    summary: str
    topics: list[str]
    filename: str

