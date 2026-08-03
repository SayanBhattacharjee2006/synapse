from pydantic import BaseModel

class DocumentProfile(BaseModel):
    summary: str | None
    topics: list[str] | None