from app.core.config import settings
from langchain_openai import ChatOpenAI
from app.ai.schema import EvaluatorResponseSchema, OptimizedQueryResponse
from app.features.documents.summary.schemas import IntermediateSummary
from app.features.documents.summary.schemas import DocumentProfile

llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini", 
        temperature=0.7,
        streaming=True
    )


structured_llm = llm.with_structured_output(EvaluatorResponseSchema)

optimized_query_llm = llm.with_structured_output(OptimizedQueryResponse)

mapper_llm = llm.with_structured_output(IntermediateSummary)

intermediate_reducer_llm = mapper_llm

final_reducer_llm = llm.with_structured_output(DocumentProfile)