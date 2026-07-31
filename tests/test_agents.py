import sys
import os
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


def test_response_agent_import():
    from agents.response_agent import get_response, get_response_stream

    assert callable(get_response)
    assert callable(get_response_stream)


def test_response_agent_token_count():
    from agents.response_agent import count_tokens_approx

    assert count_tokens_approx("Hello world") == 2
    assert count_tokens_approx("a" * 100) == 25


def test_planner_agent_all_routes():
    from agents.planner_agent import planner

    routes = {
        "CHAT": ["Hello", "Hi", "Hey", "Good morning", "Thanks", "Explain AI", "What is deep learning?"],
        "WEB": ["Latest news", "Today's weather", "Current events", "Breaking news"],
        "RESEARCH": ["Research this", "Analyze sources", "Deep dive", "Comprehensive analysis", "latest research on AI"],
        "TOOL": ["Calculate 2 + 2", "Run code", "Execute Python"],
        "RAG": ["Extract from pdf", "Summarize my uploaded notes", "Tell me about the uploaded document"]
    }
    for route, queries in routes.items():
        for query in queries:
            assert planner(query) == route, f"Failed for query: {query}"


def test_retriever_agent():
    from rag.retriever import Retriever

    retriever = Retriever()
    assert retriever is not None


def test_tool_agent_import():
    from agents.tool_agent import classify_tool

    assert callable(classify_tool)


def test_validator_agent():
    from agents.validator_agent import validate_answer_standalone

    assert validate_answer_standalone("This is a valid response") is True
    assert validate_answer_standalone("") is False
    assert validate_answer_standalone("Short") is False


def test_research_agent():
    from rag.rag_pipeline import RAGPipeline

    pipeline = RAGPipeline()
    assert pipeline is not None


def test_web_agent():
    from tools.web_search import web_search, SearchCache

    cache = SearchCache()
    assert cache is not None
    cache.set("test", {"results": []})
    assert cache.get("test") is not None


def test_pdf_tool():
    from tools.calculator import calculate

    result = calculate("2 + 2")
    assert "Result:" in result


def test_memory_manager_import():
    from memory.memory_manager import get_history

    assert callable(get_history)


def test_document_manager_import():
    from database.document_manager import DocumentManager

    dm = DocumentManager()
    assert dm is not None


def test_supabase_client_import():
    from database.supabase_client import supabase

    assert supabase is not None
