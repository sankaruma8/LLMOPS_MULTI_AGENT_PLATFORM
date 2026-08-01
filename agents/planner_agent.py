import re
from agents.response_agent import get_response


PLANNER_SYSTEM_PROMPT = """You are an intent classifier. Given a user question, determine the BEST route.

Routes:
- CHAT: Greetings, small talk, opinions, explanations from general knowledge, advice
- RAG: Questions about uploaded documents, notes, PDFs, specific content from files
- WEB: Current events, real-time info, weather, prices, recent news, facts needing fresh data

Rules:
1. If the user references "uploaded", "document", "notes", "PDF" → RAG
2. If asking about current/recent/today/live → WEB
3. Default to the most specific route

Return ONLY the route name on a single line: CHAT, RAG, or WEB"""


def planner(question: str, history: list = None) -> str:
    q = question.lower().strip()

    fast_patterns = [
        (r"^(hi|hello|hey|good\s+(morning|afternoon|evening|night)|thanks|thank\s+you|bye|ok|okay|yes|no|sure)\s*[!.?]*$", "CHAT"),
    ]
    for pattern, route in fast_patterns:
        if re.match(pattern, q):
            return route

    history_context = ""
    if history:
        recent = history[-3:]
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("message", "")[:100]
            history_context += f"{role}: {content}\n"

    prompt = (
        f"Conversation history:\n{history_context}\n" if history_context else ""
    ) + f"User question: {question}\n\nRoute:"

    try:
        response = get_response(prompt, system_prompt=PLANNER_SYSTEM_PROMPT)
        route = response.strip().upper().split()[0] if response.strip() else "RAG"

        valid_routes = {"CHAT", "RAG", "WEB"}
        if route not in valid_routes:
            route = "RAG"

        return route
    except Exception:
        return _fallback_planner(q)


def _fallback_planner(q: str) -> str:
    if any(w in q for w in ["latest", "today", "news", "weather", "current", "price"]):
        return "WEB"
    if any(w in q for w in ["hi", "hello", "hey", "thanks"]):
        return "CHAT"
    return "RAG"
