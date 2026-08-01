from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.nodes import (
    memory_node,
    planner_node,
    chat_node,
    rag_node,
    web_node,
    validator_node,
    save_node
)

workflow = StateGraph(AgentState)

workflow.add_node("memory", memory_node)
workflow.add_node("planner", planner_node)
workflow.add_node("chat", chat_node)
workflow.add_node("rag", rag_node)
workflow.add_node("web", web_node)
workflow.add_node("validator", validator_node)
workflow.add_node("save", save_node)

workflow.set_entry_point("memory")
workflow.add_edge("memory", "planner")


def route_decision(state):
    return state["route"]


workflow.add_conditional_edges(
    "planner",
    route_decision,
    {
        "CHAT": "chat",
        "RAG": "rag",
        "WEB": "web",
    },
)

workflow.add_edge("chat", "validator")
workflow.add_edge("rag", "validator")
workflow.add_edge("web", "validator")

def validator_route(state):
    if state["valid"]:
        return "SAVE"

    routes_tried = state.get("routes_tried", [])

    for route in ("RAG", "WEB"):
        if route not in routes_tried:
            return route

    return "SAVE"


workflow.add_conditional_edges(
    "validator",
    validator_route,
    {
        "SAVE": "save",
        "RAG": "rag",
        "WEB": "web",
    },
)

workflow.add_edge("save", END)

graph = workflow.compile()
