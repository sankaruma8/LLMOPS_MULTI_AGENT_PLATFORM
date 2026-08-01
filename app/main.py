import json
import time
import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from api.upload import router as upload_router
from api.auth import router as auth_router
from app.dependencies import get_current_user
from app.config import settings

app = FastAPI(
    title="LLMOps Multi-Agent Platform",
    version="1.0.0",
    description="Multi-agent platform with RAG, Web Search, and Conversational AI"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(upload_router)


@app.on_event("startup")
async def startup_event():
    print(f"Server starting in {settings.ENV} mode")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _warmup_models)
    print("Server ready - models loaded")


def _warmup_models():
    print("Loading embedding model...", flush=True)
    from rag.embeddings import EmbeddingModel
    EmbeddingModel()
    print("Loading graph workflow...", flush=True)
    from graph.workflow import graph
    assert graph is not None
    print("Models loaded.", flush=True)


class ChatRequest(BaseModel):
    session_id: str
    message: str
    stream: Optional[bool] = False


@app.get("/")
async def home():
    return {
        "message": "Welcome to LLMOps Multi-Agent Platform",
        "version": "1.0.0",
        "environment": settings.ENV,
        "endpoints": {
            "auth": {
                "signup": "POST /auth/signup",
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "me": "GET /auth/me"
            },
            "chat": "POST /chat",
            "chat_stream": "POST /chat/stream",
            "upload": "POST /upload",
            "history": "GET /history/{session_id}",
            "docs": "GET /docs"
        }
    }


@app.get("/health")
async def health_check():
    try:
        from database.supabase_client import supabase
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: supabase.table("chat_history").select("id").limit(1).execute()
        )
        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.ENV
        }
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


@app.post("/chat")
async def chat(
    request: ChatRequest,
    user: Optional[dict] = Depends(get_current_user)
):
    t0 = time.time()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _run_graph(request.session_id, request.message)
    )

    latency_ms = (time.time() - t0) * 1000

    return {
        "success": True,
        "message": "Response generated successfully",
        "data": {
            "agent": result["route"],
            "answer": result["answer"],
            "latency_ms": round(latency_ms, 2),
            "user": user["email"] if user else "anonymous"
        }
    }


def _run_graph(session_id: str, message: str) -> dict:
    from graph.workflow import graph
    return graph.invoke({
        "session_id": session_id,
        "question": message,
        "history": [],
        "route": "",
        "answer": "",
        "valid": True
    })


async def chat_stream_generator(session_id: str, message: str):
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: _run_graph(session_id, message)
        )

        answer = result["answer"]
        agent = result["route"]

        yield f"data: {json.dumps({'type': 'start', 'agent': agent})}\n\n"

        for i in range(0, len(answer), 20):
            chunk = answer[i:i+20]
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

        yield f"data: {json.dumps({'type': 'end', 'answer': answer})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        chat_stream_generator(request.session_id, request.message),
        media_type="text/event-stream"
    )


@app.get("/history/{session_id}")
async def history(
    session_id: str,
    user: Optional[dict] = Depends(get_current_user)
):
    from memory.memory_manager import get_history
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, get_history, session_id)

    return {
        "success": True,
        "data": data,
        "user": user["email"] if user else "anonymous"
    }
