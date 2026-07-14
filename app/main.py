from fastapi import FastAPI
from pydantic import BaseModel

from database.supabase_client import supabase
from database.crud import save_conversation, get_history
from agents.response_agent import get_response

app = FastAPI(
    title="LLMOps Multi-Agent Platform",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {
        "message": "Welcome to LLMOps Multi-Agent Platform"
    }


@app.get("/test-db")
def test_database():
    response = (
        supabase
        .table("users")
        .select("*")
        .limit(1)
        .execute()
    )

    return response.data


@app.post("/chat")
def chat(request: ChatRequest):
    reply = get_response(request.message)

    save_conversation(
        request.message,
        reply
    )

    return {
        "user": request.message,
        "assistant": reply
    }


@app.get("/history")
def history():
    return get_history()