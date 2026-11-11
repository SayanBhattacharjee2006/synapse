from pydantic import BaseModel

from app.contracts.document_profile import DocumentProfile


class IntermediateSummary(BaseModel):
    summary: str


__all__ = ["DocumentProfile", "IntermediateSummary"]
