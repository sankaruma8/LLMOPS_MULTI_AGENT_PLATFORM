# API Reference

Base URL: `http://localhost:8000` (configured via `BACKEND_URL` on the frontend). Interactive docs are auto-generated at `/docs`.

Auth endpoints accept JSON bodies. Protected/optional-auth endpoints read a Bearer token from the `Authorization` header.

---

## System

### `GET /`
Service info and endpoint map.

**Response:** `200`
```json
{
  "message": "Welcome to LLMOps Multi-Agent Platform",
  "version": "1.0.0",
  "environment": "development",
  "endpoints": { "chat": "POST /chat", "upload": "POST /upload", "...": "..." }
}
```

### `GET /health`
Checks database connectivity.

**Response:** `200`
```json
{ "status": "healthy", "database": "connected", "environment": "development" }
```
When the database is unreachable or keys are invalid:
```json
{ "status": "unhealthy", "database": "Invalid API key" }
```

---

## Auth

### `POST /auth/signup`
Create an account.

**Body:**
```json
{ "email": "user@example.com", "password": "secret123", "full_name": "Jane Doe" }
```

**Response:** `200`
```json
{
  "success": true,
  "message": "Account created successfully",
  "data": { "user": { "id": "...", "email": "user@example.com", "full_name": "Jane Doe" },
            "access_token": "<jwt>", "token_type": "bearer" }
}
```

Errors: `409` email already registered, `500` other failures.

### `POST /auth/login`
**Body:** `{ "email": "...", "password": "..." }`

**Response:** `200` — `access_token`, `refresh_token`, `token_type`, `expires_in`, plus the user object.

### `POST /auth/refresh`
**Body:** `{ "refresh_token": "..." }`

**Response:** `200` — new `access_token` + `refresh_token`.

### `POST /auth/logout`
Header: `Authorization: Bearer <token>`

**Response:** `200` — `{ "success": true, "message": "Logged out successfully" }`

### `GET /auth/me`
Header: `Authorization: Bearer <token>`

**Response:** `200` — user object (`id`, `email`, `full_name`, `created_at`, `last_login`).

### `PUT /auth/profile`
Header: `Authorization: Bearer <token>` · Query param: `?full_name=New Name`

**Response:** `200` — `{ "success": true, "message": "Profile updated successfully" }`

---

## Chat

### `POST /chat`
Send a message. The message is routed automatically to Chat, RAG, or Web.

**Body:**
```json
{ "session_id": "streamlit_123", "message": "What is a transformer?", "stream": false }
```

**Response:** `200`
```json
{
  "success": true,
  "message": "Response generated successfully",
  "data": {
    "agent": "RAG",
    "answer": "A transformer is a neural network architecture...",
    "latency_ms": 1842.11,
    "user": "anonymous"
  }
}
```

`user` is the authenticated user's email, or `"anonymous"` when no token is sent.

### `POST /chat/stream`
Same body. Returns a `text/event-stream`:
```
data: {"type": "start", "agent": "RAG"}
data: {"type": "chunk", "content": "A transformer is "}
data: {"type": "chunk", "content": "a neural network..."}
data: {"type": "end", "answer": "..."}
```
On error: `data: {"type": "error", "message": "..."}`.

### `GET /history/{session_id}`
Returns conversation history for a session.

**Response:** `200`
```json
{
  "success": true,
  "data": [ { "session_id": "...", "role": "user", "message": "...", "created_at": "..." } ],
  "user": "anonymous"
}
```

---

## Documents

### `POST /upload`
Upload a PDF (multipart form). Required field: `file`. Optional: `session_id`.

**Response:** `200` — new upload:
```json
{
  "success": true,
  "message": "PDF uploaded and indexed",
  "data": { "status": "new", "filename": "notes.pdf", "version": 1,
            "chunks": 73, "pages": 26, "file_size": 1363148, "doc_id": "..." }
}
```
Duplicate upload:
```json
{ "success": true, "message": "Document already exists",
  "data": { "status": "duplicate", "existing_document": { "filename": "notes.pdf", "version": 1 } } }
```

Errors: `400` non-PDF or no extractable text.

### `POST /upload/batch`
Multiple PDFs (`files: [File]`, `session_id` optional). Returns per-file results plus totals.

### `GET /upload/list`
List documents. Optional query param: `?session_id=...`

**Response:** `200` — `{ "success": true, "data": [ ... ], "count": N }`

### `GET /documents`
Alias for listing. Returns `{ "success": true, "data": { "documents": [...], "count": N } }`.

### `GET /documents/stats`
Storage + vector stats:
```json
{ "success": true, "data": { "database": { "total_documents": 7, "total_chunks": 215, "total_size_mb": 12.4 },
                             "vectors": { "total_chunks": 215, "files": 7 } } }
```

### `GET /documents/{filename}/history`
Version history for a document.

### `DELETE /documents/{filename}`
Deletes chunks and metadata for a document.
