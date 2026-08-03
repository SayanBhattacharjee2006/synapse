from app.features.documents.summary.prompts import get_mapper_prompt 
from langchain_core.documents import Document
from app.features.documents.summary.schemas import IntermediateSummary
from app.ai.llm import mapper_llm
from app.features.documents.formatter import group_serializer


async def summarize_group(chunk_group: list[Document])-> IntermediateSummary:
    serialized_group = group_serializer(chunk_group)

    prompt = get_mapper_prompt(serialized_group)

    response = await mapper_llm.ainvoke(prompt) 

    return response