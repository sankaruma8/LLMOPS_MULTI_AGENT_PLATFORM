from typing import TypedDict, Optional


class AgentState(TypedDict):
    session_id: str
    question: str
    history: list
    route: str
    answer: str
    valid: bool
    sources: Optional[list]
    rag_context: Optional[str]
    web_context: Optional[str]
    available_docs: Optional[list]
    routes_tried: Optional[list]
