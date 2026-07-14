from database.supabase_client import supabase


def save_conversation(user_message, assistant_message):
    data = {
        "user_message": user_message,
        "assistant_message": assistant_message
    }

    supabase.table("conversations").insert(data).execute()
def get_history():
    response = (
        supabase
        .table("conversations")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data    
