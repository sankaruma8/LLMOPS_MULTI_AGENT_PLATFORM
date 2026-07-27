from datetime import datetime
from typing import Optional, List
from database.supabase_client import supabase
from agents.response_agent import get_response


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

    def get_sliding_window(self, session_id: str) -> List[dict]:

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

    def count_tokens_approx(self, text: str) -> int:

        return len(text) // 4

    def fit_history_to_tokens(self, history: List[dict]) -> List[dict]:

        total_tokens = 0
        fitted = []

        for msg in reversed(history):
            msg_tokens = self.count_tokens_approx(msg.get("message", ""))

            if total_tokens + msg_tokens > self.max_tokens:
                break

            fitted.insert(0, msg)
            total_tokens += msg_tokens

        return fitted

    def summarize_old_messages(self, messages: List[dict]) -> str:

        if not messages:
            return ""

        history_text = ""
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("message", "")
            history_text += f"{role}: {content}\n"

        prompt = (
            "Summarize the following conversation history in 2-3 sentences. "
            "Focus on key topics, decisions, and important information.\n\n"
            f"Conversation:\n{history_text}\n\n"
            "Summary:"
        )

        try:
            summary = get_response(prompt)
            return summary
        except Exception as e:
            print(f"Summarization failed: {e}")

            recent = messages[-3:]
            return self.format_history_for_prompt(recent)

    def get_optimized_history(self, session_id: str) -> List[dict]:

        all_history = self.get_history(session_id)

        if len(all_history) <= 10:
            return all_history

        old_messages = all_history[:-10]
        recent_messages = all_history[-10:]

        summary = self.summarize_old_messages(old_messages)

        optimized = [
            {
                "role": "system",
                "message": f"Previous conversation summary: {summary}"
            }
        ]

        optimized.extend(recent_messages)

        return optimized

    def save_user_memory(self, user_id: str, memory_type: str, content: str, metadata: dict = None):

        data = {
            "user_id": user_id,
            "memory_type": memory_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        response = supabase.table("user_memory").insert(data).execute()
        return response.data[0] if response.data else None

    def get_user_memories(self, user_id: str, memory_type: Optional[str] = None) -> List[dict]:

        query = (
            supabase
            .table("user_memory")
            .select("*")
            .eq("user_id", user_id)
        )

        if memory_type:
            query = query.eq("memory_type", memory_type)

        query = query.order("created_at", desc=True)

        response = query.execute()
        return response.data if response.data else []

    def update_user_memory(self, memory_id: str, content: str, metadata: dict = None):

        update_data = {
            "content": content,
            "updated_at": datetime.utcnow().isoformat()
        }

        if metadata:
            update_data["metadata"] = metadata

        supabase.table("user_memory").update(update_data).eq("id", memory_id).execute()

    def delete_user_memory(self, memory_id: str):

        supabase.table("user_memory").delete().eq("id", memory_id).execute()

    def search_user_memories(self, user_id: str, query: str) -> List[dict]:

        all_memories = self.get_user_memories(user_id)

        query_lower = query.lower()
        scored_memories = []

        for memory in all_memories:
            content = memory.get("content", "").lower()
            score = 0

            query_words = query_lower.split()
            for word in query_words:
                if word in content:
                    score += 1

            if score > 0:
                scored_memories.append((score, memory))

        scored_memories.sort(key=lambda x: x[0], reverse=True)

        return [memory for _, memory in scored_memories[:5]]

    def build_context_with_memory(self, session_id: str, user_id: Optional[str] = None) -> dict:

        session_history = self.get_optimized_history(session_id)

        user_memories = []
        if user_id:
            user_memories = self.search_user_memories(user_id, session_history[-1].get("message", "") if session_history else "")

        return {
            "session_history": session_history,
            "user_memories": user_memories,
            "formatted_history": self.format_history_for_prompt(session_history)
        }


memory_manager = MemoryManager()


def save_message(session_id: str, role: str, message: str):
    memory_manager.save_message(session_id, role, message)


def get_history(session_id: str) -> List[dict]:
    return memory_manager.get_optimized_history(session_id)


def get_sliding_window(session_id: str) -> List[dict]:
    return memory_manager.get_sliding_window(session_id)


def get_formatted_history(session_id: str) -> str:
    history = memory_manager.get_optimized_history(session_id)
    return memory_manager.format_history_for_prompt(history)


def save_user_preference(user_id: str, key: str, value: str):
    return memory_manager.save_user_memory(user_id, "preference", f"{key}: {value}")


def save_user_fact(user_id: str, fact: str):
    return memory_manager.save_user_memory(user_id, "fact", fact)


def get_user_context(user_id: str) -> List[dict]:
    return memory_manager.get_user_memories(user_id)
