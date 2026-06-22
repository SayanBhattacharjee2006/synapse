from app.core.config import settings
from langchain_openai import ChatOpenAI
from app.ai.schema import EvaluatorResponseSchema 
llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini", 
        temperature=0.7,
        streaming=True
    )


structured_llm = llm.with_structured_output(EvaluatorResponseSchema)
