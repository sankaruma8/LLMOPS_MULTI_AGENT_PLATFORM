from typing import TypedDict, Optional


class AgentState(TypedDict):
    session_id: str
    question: str
    history: list
    route: str
    answer: str
    valid: bool
    sources: Optional[list]
    tool_used: Optional[str]
    latency_ms: Optional[float]
    rag_context: Optional[str]
    web_context: Optional[str]
    available_docs: Optional[list]
    routes_tried: Optional[list]
