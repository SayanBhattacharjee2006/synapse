from app.core.config import settings
from tavily import AsyncTavilyClient

tavily_client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

async def search_tavily(query: str) -> str:
    response = await tavily_client.search(query, max_results=5, language="en")
    return response

def create_search_response(response):
    context = ""

    for idx, result in enumerate(response.get("results", [])):
        context += (
            f"Result {idx + 1}:\n"
            f"Title: {result.get('title', '')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Content: {result.get('content', '')}\n\n"
        )

    return context