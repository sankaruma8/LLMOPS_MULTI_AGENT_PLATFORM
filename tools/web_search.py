import time
import hashlib
import json
from typing import Optional
from tavily import TavilyClient
from app.config import settings


class SearchCache:

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 100):
        self.cache = {}
        self.ttl = ttl_seconds
        self.max_size = max_size

    def _make_key(self, query: str, **kwargs) -> str:
        key_data = json.dumps({"query": query, **kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, **kwargs) -> Optional[dict]:
        key = self._make_key(query, **kwargs)

        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
            else:
                del self.cache[key]

        return None

    def set(self, query: str, data: dict, **kwargs):
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache, key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        key = self._make_key(query, **kwargs)
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }

    def clear(self):
        self.cache.clear()

    def size(self):
        return len(self.cache)


cache = SearchCache(ttl_seconds=3600)

tavily_client = None


def get_tavily_client():
    global tavily_client
    if tavily_client is None:
        tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return tavily_client


def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "advanced",
    use_cache: bool = True
) -> dict:

    if use_cache:
        cached = cache.get(query, max_results=max_results, search_depth=search_depth)
        if cached:
            print(f"Cache hit for query: {query[:50]}...")
            return cached

    try:
        client = get_tavily_client()

        result = client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results
        )

        formatted = {
            "query": query,
            "results": result.get("results", []),
            "answer": result.get("answer", ""),
            "follow_up_questions": result.get("follow_up_questions", []),
            "cached": False
        }

        if use_cache:
            cache.set(query, formatted, max_results=max_results, search_depth=search_depth)

        return formatted

    except Exception as e:
        return {
            "query": query,
            "results": [],
            "answer": "",
            "error": str(e),
            "cached": False
        }


def get_cached_queries() -> list:
    queries = []
    for key, entry in cache.cache.items():
        queries.append({
            "query": entry["data"].get("query", "unknown"),
            "timestamp": entry["timestamp"],
            "result_count": len(entry["data"].get("results", []))
        })
    return queries


def clear_search_cache():
    cache.clear()
    return {"message": "Search cache cleared", "size": cache.size()}
