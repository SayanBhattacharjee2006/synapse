from langchain_core.documents import Document

from app.ai.llm import mapper_llm
from app.ai.rag.summarization.formatter import group_serializer
from app.ai.rag.summarization.prompts import get_mapper_prompt
from app.ai.rag.summarization.schemas import IntermediateSummary


async def summarize_group(chunk_group: list[Document]) -> IntermediateSummary:
    serialized_group = group_serializer(chunk_group)
    prompt = get_mapper_prompt(serialized_group)
    response = await mapper_llm.ainvoke(prompt)
    return response

