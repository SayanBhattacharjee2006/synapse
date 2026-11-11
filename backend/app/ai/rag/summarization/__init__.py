from app.ai.rag.summarization.schemas import (
    DocumentProfile,
    IntermediateSummary,
)


def __getattr__(name: str):
    if name == "generate_document_profile":
        from app.ai.rag.summarization.service import generate_document_profile

        return generate_document_profile
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DocumentProfile",
    "IntermediateSummary",
    "generate_document_profile",
]
