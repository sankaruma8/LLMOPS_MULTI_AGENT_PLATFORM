from database.supabase_client import supabase


def save_conversation(session_id, user_message, assistant_message):
    supabase.table("chat_history").insert({
        "session_id": session_id,
        "role": "user",
        "message": user_message
    }).execute()

    supabase.table("chat_history").insert({
        "session_id": session_id,
        "role": "assistant",
        "message": assistant_message
    }).execute()


def get_history(session_id):
    response = (
        supabase
        .table("chat_history")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )

    return response.data
