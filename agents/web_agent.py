from tavily import TavilyClient
from app.config import settings
from agents.response_agent import get_response


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


def web_search(query: str):

    results = search_web(query)

    if not results:
        return "I couldn't find any relevant web results for your query."

    context = format_web_results(results)

    system_prompt = (
        "You are a helpful assistant that answers questions based on web search results. "
        "Use ONLY the provided search results to answer. "
        "If the results don't contain enough information, say so. "
        "Always cite the source URL when possible."
    )

    prompt = (
        f"Search Results:\n{context}\n"
        f"Question: {query}\n\n"
        f"Provide a comprehensive answer based on the search results above:"
    )

    return get_response(prompt, system_prompt=system_prompt)
