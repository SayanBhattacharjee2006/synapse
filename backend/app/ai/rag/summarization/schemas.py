from pydantic import BaseModel


class IntermediateSummary(BaseModel):
    summary: str
