from typing import Optional, List
from database.supabase_client import supabase


class MemoryManager:

    def __init__(self, max_history: int = 20, max_tokens: int = 3000):
        self.max_history = max_history
        self.max_tokens = max_tokens

    def save_message(self, session_id: str, role: str, message: str):
        supabase.table("chat_history").insert({
            "session_id": session_id,
            "role": role,
            "message": message
        }).execute()

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[dict]:
        query = (
            supabase
            .table("chat_history")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
        )

        if limit:
            query = query.limit(limit)

        response = query.execute()
        return response.data if response.data else []

    def get_optimized_history(self, session_id: str) -> List[dict]:
        all_history = self.get_history(session_id)

        if len(all_history) <= self.max_history:
            return all_history

        return all_history[-self.max_history:]

    def format_history_for_prompt(self, history: List[dict]) -> str:
        if not history:
            return ""

        formatted = []
        for msg in history:
            role = msg.get("role", "user").capitalize()
            content = msg.get("message", "")
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)


memory_manager = MemoryManager()


def save_message(session_id: str, role: str, message: str):
    memory_manager.save_message(session_id, role, message)


def get_history(session_id: str) -> List[dict]:
    return memory_manager.get_optimized_history(session_id)


def get_formatted_history(session_id: str) -> str:
    history = memory_manager.get_optimized_history(session_id)
    return memory_manager.format_history_for_prompt(history)
