from app.core.config import settings
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini", 
        temperature=0.7,
        streaming=True
    )
