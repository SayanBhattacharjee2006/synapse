from profile import DocumentProfile

def format_document_profile(document_profile: DocumentProfile) -> str:
    summary = document_profile.summary or "No summary available."
    topics = ", ".join(document_profile.topics) if document_profile.topics else "No topics available."
    return f"""
    Summary: {summary}
    Topics: {topics}
"""