from graph.workflow import graph
from agents.planner_agent import planner, _fallback_planner


def test_graph_compiles():
    assert graph is not None


def test_planner_fast_path():
    assert planner("hello") == "CHAT"


def test_planner_fallback_routes():
    assert _fallback_planner("what is the latest news") == "WEB"
    assert _fallback_planner("hi there") == "CHAT"
    assert _fallback_planner("summarize my uploaded notes") == "RAG"


def test_planner_returns_valid_route():
    assert planner("explain machine learning") in {"CHAT", "RAG", "WEB"}
