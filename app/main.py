import json
import time
import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from api.upload import router as upload_router
from api.auth import router as auth_router
from middleware.rate_limiter import RateLimitMiddleware, rate_limiter
from app.dependencies import get_current_user
from monitoring.metrics import metrics, tracker, sync_prometheus_metrics
from core import config_manager
from typing import Optional

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


def _add_prometheus(app):
    try:
        from monitoring.prometheus_metrics import PrometheusMiddleware
        app.add_middleware(PrometheusMiddleware)
    except Exception as e:
        print(f"Prometheus middleware not enabled: {e}")


_add_prometheus(app)


@app.on_event("startup")
async def startup_event():
    print(f"Server starting in {config_manager.env.value} mode")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _warmup_models)
    print("Server ready - models loaded")


def _warmup_models():
    print("Loading embedding model...", flush=True)
    from rag.embeddings import EmbeddingModel
    EmbeddingModel()
    print("Loading graph workflow...", flush=True)
    from graph.workflow import graph
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
        "environment": config_manager.env.value,
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
            "monitoring": {
                "metrics": "GET /metrics",
                "prometheus": "GET /prometheus/metrics",
                "system": "GET /system/status"
            },
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
            lambda: supabase.table("user_memory").select("id").limit(1).execute()
        )
        return {
            "status": "healthy",
            "database": "connected",
            "environment": config_manager.env.value,
            "uptime": metrics.get_uptime(),
            "total_queries": metrics._query_count
        }
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


@app.post("/chat")
async def chat(
    request: ChatRequest,
    user: Optional[dict] = Depends(get_current_user)
):
    from core.security import InputSanitizer, security_middleware
    from core.security import audit_logger

    validation = security_middleware.validate_request({
        "session_id": request.session_id,
        "message": request.message
    })

    if not validation["valid"]:
        audit_logger.log(
            action="chat.rejected",
            user_id=user["email"] if user else "anonymous",
            details={"errors": validation["errors"], "message_length": len(request.message)}
        )
        return {"success": False, "errors": validation["errors"]}

    sanitized_message = InputSanitizer.sanitize_text(request.message)

    t0 = time.time()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _run_graph(request.session_id, sanitized_message)
    )

    latency_ms = (time.time() - t0) * 1000

    metrics.record_query(
        route=result["route"],
        latency_ms=latency_ms,
        is_valid=True,
        agent_name=result["route"]
    )

    audit_logger.log(
        action="chat.completed",
        user_id=user["email"] if user else "anonymous",
        resource=result["route"],
        details={
            "message_length": len(sanitized_message),
            "response_length": len(result["answer"]),
            "latency_ms": round(latency_ms, 2)
        }
    )

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


@app.get("/metrics")
async def get_metrics():
    return {
        "success": True,
        "data": metrics.get_summary()
    }


@app.get("/prometheus/metrics")
async def get_prometheus_metrics():
    from fastapi.responses import Response
    from monitoring.prometheus_metrics import metrics_response
    sync_prometheus_metrics()
    body, content_type = metrics_response()
    return Response(content=body, media_type=content_type)


@app.get("/system/status")
async def system_status():
    return {
        "success": True,
        "data": {
            "environment": config_manager.env.value,
            "features": {
                "auth": config_manager.config.features.enable_auth,
                "rate_limiting": config_manager.config.features.enable_rate_limiting,
                "monitoring": config_manager.config.features.enable_monitoring,
                "streaming": config_manager.config.features.enable_streaming,
                "caching": config_manager.config.features.enable_caching
            }
        }
    }


@app.get("/system/audit")
async def system_audit(
    limit: int = 100,
    action: Optional[str] = None,
    user_id: Optional[str] = None
):
    from core.security import audit_logger
    entries = audit_logger.get_entries(
        user_id=user_id,
        action=action,
        limit=max(1, min(limit, 1000))
    )
    return {"success": True, "data": entries}


@app.get("/system/audit/stats")
async def system_audit_stats():
    from core.security import audit_logger
    return {"success": True, "data": audit_logger.get_stats()}


@app.get("/cache/stats")
async def cache_stats():
    from rag.embeddings import embedding_cache
    from tools.web_search import get_cached_queries
    return {
        "success": True,
        "data": {
            "embedding_cache_size": embedding_cache.size(),
            "web_search_cache": get_cached_queries()
        }
    }


@app.post("/cache/clear")
async def clear_cache():
    from rag.embeddings import embedding_cache
    from tools.web_search import clear_search_cache
    embedding_cache.clear()
    clear_search_cache()
    return {"success": True, "message": "All caches cleared"}


@app.get("/rate-limit/stats")
async def rate_limit_stats():
    return {"success": True, "data": rate_limiter.get_stats()}


@app.post("/metrics/reset")
async def reset_metrics():
    metrics.reset()
    return {"success": True, "message": "Metrics reset successfully"}
