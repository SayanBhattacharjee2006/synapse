from langchain_core.documents import Document
from app.features.documents.summary.tiktoken import get_token_count
from langchain_core.documents import Document
from app.features.documents.summary.schemas import IntermediateSummary

def group_by_tokens(items: list[Document] | list[IntermediateSummary], text_extractore, threshold: int)-> list[list[Document]] | list[list[IntermediateSummary]]:

    current_token_count = 0
    current_group: list[Document] | list[IntermediateSummary] = []
    groups: list[list[Document]] | list[list[IntermediateSummary]] = []

    for item in items:
        chunk_token_count = get_token_count(text_extractore(item))

        if current_token_count + chunk_token_count > threshold:    
            if current_group:
                groups.append(current_group)
            current_group = []
            current_token_count = 0

        current_group.append(item)
        current_token_count += chunk_token_count

    if current_group:
        groups.append(current_group)

    return groups