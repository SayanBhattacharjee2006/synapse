from pydantic import BaseModel, Field


class RetrievalEvalSchema(BaseModel):
    relevance: int = Field(
        ...,
        ge=0,
        le=5,
        description=(
            "How relevant the retrieved context is to the user's question. "
            "Higher scores mean the retrieved context directly contains "
            "information useful for answering the question."
        ),
    )

    completeness: int = Field(
        ...,
        ge=0,
        le=5,
        description=(
            "How completely the retrieved context contains the information "
            "needed to answer the user's question. Higher scores mean the "
            "retrieved context contains all or nearly all required evidence."
        ),
    )