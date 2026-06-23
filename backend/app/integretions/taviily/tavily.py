from app.core.config import settings
from tavily import AsyncTavilyClient

tavily_client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

async def search_tavily(query: str) -> str:
    response = await tavily_client.search(query, max_results=5, language="en")
    return response

def create_search_response(response):
    context = ""

    for idx, result in enumerate(response["results"]):
        if result['score'] > 0.7:
            context += f"Result {idx + 1}:\nTitle: {result['title']}\nURL: {result['url']}\ncontent: {result['content']}\n\n"

    return context