from typing import List
from pydantic import  BaseModel, Field
from app.ai.schema import RouterType

class ReferenceEvidenceSchema(BaseModel):
    doc: List[str] = Field(description="List of document IDs supporting the reference answer")
    web: List[str] = Field(description="Reference web sources (Optional)")
class DataSetSchema(BaseModel):
    question: str = Field(...,description="The question or query asked by the user")
    expected_route : RouterType = Field(...,description="The route selected by the router for this query")
    reference_answer : str = Field(...,description="The expected answer for the asked question or query")
    reference_evidence : ReferenceEvidenceSchema | None = Field(description="expected (optional) evidence sources")