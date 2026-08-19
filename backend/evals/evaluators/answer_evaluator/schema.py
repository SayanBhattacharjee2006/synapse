from pydantic import BaseModel, Field


class AnswerEvalSchema(BaseModel):
    correctness: int = Field(
        ...,
        ge=0,
        le=5,
        description="Correctness of the answer compared with the reference answer (0-5 scale).",
    )

    relevance: int = Field(
        ...,
        ge=0,
        le=5,
        description="How directly and appropriately the answer addresses the question (0-5 scale).",
    )

    groundedness: int | None = Field(
        default=None,
        ge=0,
        le=5,
        description="How well the answer is supported by the provided context. None when grounding is not applicable.",
    )

    overall: int = Field(
        ...,
        ge=0,
        le=5,
        description="Overall quality of the answer (0-5 scale).",
    )

    reason: str = Field(
        ...,
        description="Brief explanation supporting the evaluation scores.",
    )
