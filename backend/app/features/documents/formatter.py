from app.features.documents.summary.schemas import DocumentProfile
from langchain_core.documents import Document

def format_document_profile(document_profile: DocumentProfile) -> str:
    summary = document_profile.summary or "No summary available."
    topics = ", ".join(document_profile.topics) if document_profile.topics else "No topics available."
    return f"""
    Summary: {summary}
    Topics: {topics}
"""

def group_serializer(chunk_group: list[Document])-> str:
    serialized_parts = []
    serialized_parts.append(f"The following document section consists of {len(chunk_group)} consecutive chunks extracted from the same document.\n")
    for idx, chunk in enumerate(chunk_group):
        serialized_parts.append(f"========Chunk {idx + 1}=========\n{chunk.page_content}\n")

    return "".join(serialized_parts)



        