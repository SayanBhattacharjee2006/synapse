from app.core.config import settings
from langchain_openai import ChatOpenAI

from app.ai.schema import EvaluatorResponseSchema
from app.features.documents.summary.schemas import IntermediateSummary
from app.features.documents.summary.schemas import DocumentProfile


llm = ChatOpenAI(
    api_key=settings.OPENAI_API_KEY,
    model="gpt-4o-mini",
    temperature=0.7,
    streaming=True,
)

llm2 = ChatOpenAI(
    api_key=settings.OPENAI_API_KEY,
    model="gpt-4o-mini",
    temperature=0,
)

router_llm = llm2.with_structured_output(
    EvaluatorResponseSchema
)

mapper_llm = llm.with_structured_output(
    IntermediateSummary
)

intermediate_reducer_llm = mapper_llm

final_reducer_llm = llm.with_structured_output(
    DocumentProfile
)