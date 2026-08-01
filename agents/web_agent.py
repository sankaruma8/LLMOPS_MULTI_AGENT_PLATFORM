from tavily import TavilyClient
from app.config import settings


tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


def search_web(query: str, max_results: int = 5):

    result = tavily_client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results
    )

    return result.get("results", [])


def format_web_results(results: list) -> str:

    context = ""
    for item in results:
        context += (
            f"Title: {item['title']}\n"
            f"Content: {item['content']}\n"
            f"URL: {item['url']}\n\n"
        )
    return context
