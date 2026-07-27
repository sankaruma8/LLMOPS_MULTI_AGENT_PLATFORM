from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    session_id: str
    role: str
    message: str
    created_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    success: bool
    message: str
    data: dict


class DocumentMetadata(BaseModel):
    id: Optional[str] = None
    filename: str
    file_hash: str
    session_id: str
    chunk_count: int = 0
    version: int = 1
    upload_date: Optional[datetime] = None
    file_size: int = 0
    page_count: int = 0


class UploadResponse(BaseModel):
    success: bool
    message: str
    data: dict


class AgentResponse(BaseModel):
    agent: str
    answer: str
    sources: Optional[List[str]] = None
    latency_ms: Optional[float] = None


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class UserMemory(BaseModel):
    id: Optional[str] = None
    user_id: str
    memory_type: str
    content: str
    metadata: Optional[dict] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QueryLog(BaseModel):
    id: Optional[str] = None
    session_id: str
    question: str
    route: str
    answer: Optional[str] = None
    latency_ms: Optional[float] = None
    token_count: Optional[int] = None
    is_valid: bool = True
    created_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    database: str
