from app.features.documents.summary.schemas import IntermediateSummary
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



def summary_serializer(intermediate_summaries: list[IntermediateSummary]) -> str:
    serialized_parts = []
    if len(intermediate_summaries) == 1:
        serialized_parts.append(f"The Final Intermediate Summary: .\n")
    else:
        serialized_parts.append(f"The following summary section consists of {len(intermediate_summaries)} consecutive summaries extracted from the same document.\n")
    for idx, summary in enumerate(intermediate_summaries):
        serialized_parts.append(f"========Summary {idx + 1}=========\n{summary.summary}\n")

    return "".join(serialized_parts)

