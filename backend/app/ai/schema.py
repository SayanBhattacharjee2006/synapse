from pydantic import BaseModel
from enum import Enum
from uuid import UUID


class RouterType(str, Enum):
    RAG = "rag"
    WEB = "web"
    BOTH = "both"
    NONE = "none"


class EvaluatorResponseSchema(BaseModel):
    router: RouterType
    rag_query: str | None = None
    web_query: str | None = None


class DocumentAwareWebQuerySchema(BaseModel):
    web_query: str



class DocumentSummarySchema(BaseModel):
    document_id: UUID
    conversation_id: str
    user_id: UUID
    summary: str
    topics: list[str]
    filename: str
