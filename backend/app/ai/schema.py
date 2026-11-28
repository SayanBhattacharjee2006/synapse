from enum import Enum
from pydantic import BaseModel


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


__all__ = [
    "RouterType",
    "EvaluatorResponseSchema",
    "DocumentAwareWebQuerySchema",
]
