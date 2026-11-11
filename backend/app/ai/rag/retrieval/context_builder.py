from typing import Any


def build_context(docs: list[Any]) -> str:
    """Construct formatted text context from retrieved Qdrant chunk points."""
    return "\n\n--\n\n".join(
        doc.payload.get("page_content", "")
        for doc in docs
        if getattr(doc, "payload", None) and doc.payload.get("page_content")
    )


create_context = build_context

