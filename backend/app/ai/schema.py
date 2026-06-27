from pydantic import BaseModel
from enum import Enum

class RouterType(str, Enum):
    RAG = "rag"
    WEB = "web"
    BOTH = "both"
    NONE = "none"

class EvaluatorResponseSchema(BaseModel):
    router : RouterType
    reasoning : str
    confidence: float

class OptimizedQueryResponse(BaseModel):
    rag_query: str
    web_query: str
    reasoning: str