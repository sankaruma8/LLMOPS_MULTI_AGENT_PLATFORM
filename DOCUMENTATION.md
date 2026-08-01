# LLMOps Multi-Agent Platform — Complete Documentation

**Version:** 1.0.0  
**Repository:** https://github.com/sankaruma8/LLMOPS_MULTI_AGENT_PLATFORM

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Features](#2-features)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Prerequisites](#5-prerequisites)
6. [Installation and Setup](#6-installation-and-setup)
7. [Configuration](#7-configuration)
8. [Running the Application](#8-running-the-application)
9. [Testing](#9-testing)
10. [API Reference](#10-api-reference)
11. [User Guide](#11-user-guide)
12. [Deployment](#12-deployment)
13. [Security Considerations](#13-security-considerations)
14. [Troubleshooting](#14-troubleshooting)
15. [Project Structure](#15-project-structure)
16. [Conclusion](#16-conclusion)

---

## 1. Introduction

The **LLMOps Multi-Agent Platform** is a prompt-refinement and multi-agent orchestration system. Its purpose is to improve the quality of responses produced by generative AI models by transforming a raw user question into a structured, well-scoped task and dispatching it to the most appropriate specialist agent.

Rather than sending every prompt to a single generic model call, the platform:

1. **Classifies intent** — determines whether the user needs general conversation, an answer grounded in their uploaded documents, or up-to-date web information.
2. **Routes the task** — to the matching agent: **Chat**, **RAG** (document question-answering), or **Web Search**.
3. **Grounds the answer** — injects relevant context (conversation history, document chunks, or live search results) into a purpose-built prompt so the answer is accurate and citable.
4. **Validates the output** — rejects empty, generic, or failed answers.
5. **Retries automatically** — falls back to another source when validation fails, within a bounded number of attempts.

The platform is designed for study and demonstration. It demonstrates how orchestration, retrieval-augmented generation, and prompt refinement combine to produce more reliable AI outputs.

---

## 2. Features

| Feature | Description |
|---------|-------------|
| Multi-agent orchestration | A LangGraph state machine routes each question to Chat, RAG, or Web with automatic fallback. |
| Retrieval-Augmented Generation (RAG) | Upload PDFs; they are extracted, chunked, embedded, and indexed for semantic retrieval with citations. |
| Live web search | Real-time, up-to-date answers with source URLs via the Tavily API. |
| Conversation memory | Persistent chat history stored in Supabase, injected into prompts as context (sliding window). |
| Account authentication | Email/password signup and login backed by Supabase Auth, with JWT tokens. |
| Document management | Upload, batch upload, versioning, duplicate detection, and deletion. |
| Streaming responses | Server-sent events support for token streaming from the API. |
| Graceful degradation | Unavailable databases or LLM providers never crash a request. |
| Web interface | A Streamlit dashboard for chatting and managing documents. |

---

## 3. System Architecture

The application is a client–server system with three main layers: a Streamlit frontend, a FastAPI backend, and a LangGraph orchestration engine.

```
Streamlit (frontend)
      │  HTTP / JSON
      ▼
FastAPI  (app/main.py)
      │
      ▼
LangGraph workflow  (graph/workflow.py)
      │
      ├─ MEMORY ──► PLANNER ──► { CHAT | RAG | WEB } ──► VALIDATOR ──► SAVE
      │                                                     │ retry
      ▼                                                     └────────┘
  Supabase (history, users, docs)      ChromaDB (chunks)   Tavily / Groq / OpenAI
```

### 3.1 Orchestration Workflow

The core is a **Directed Acyclic Graph** built with LangGraph's `StateGraph`. Every node reads and updates a shared `AgentState`.

| Node | Responsibility |
|------|----------------|
| **MEMORY** | Loads the last N conversation messages from Supabase and lists documents available in ChromaDB. |
| **PLANNER** | Classifies intent into `CHAT`, `RAG`, or `WEB`. Uses a regex fast-path for greetings and an LLM classification otherwise, with a keyword fallback if the LLM is unavailable. |
| **CHAT** | Answers from general knowledge, injecting conversation history and the list of available documents. |
| **RAG** | Embeds the question, retrieves the top 8 chunks by cosine similarity from ChromaDB, and answers with document and page citations. |
| **WEB** | Searches the Tavily API, formats results, and answers with source URLs. |
| **VALIDATOR** | Quality gate: rejects empty, too-short, or failure-phrase answers (for example, "sorry, I couldn't find"). |
| **SAVE** | Persists the user question and assistant answer to Supabase. |

**Fallback behaviour:** if the validator rejects an answer, the workflow retries the other source (`RAG` ↔ `WEB`, at most two retries) before saving and terminating. This keeps worst-case execution bounded and predictable.

### 3.2 RAG Pipeline

```
PDF upload
   → pypdf text extraction          (rag/document_loader.py)
   → chunking ~500 chars / 50 overlap (rag/text_splitter.py)
   → embeddings (all-MiniLM-L6-v2)   (rag/embeddings.py)
   → ChromaDB persistent store       (rag/vector_store.py)

Query
   → embed question
   → cosine-similarity search        (rag/retriever.py)
   → top 8 chunks → refined prompt → answer with citations
```

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Streamlit | Chat and document-management UI |
| API | FastAPI + Uvicorn | REST endpoints and server-sent events |
| Orchestration | LangGraph | State-machine workflow and routing |
| Primary LLM | Groq (`llama-3.3-70b-versatile`) | Intent classification and answer generation |
| Fallback LLM | OpenAI (`gpt-4o`) | Backup provider when Groq is unavailable |
| Embeddings | Sentence-Transformers `all-MiniLM-L6-v2` | Semantic representations (384 dimensions) |
| Vector store | ChromaDB | Persistent storage of document chunks |
| Database | Supabase (PostgreSQL) | Users, chat history, document metadata |
| Authentication | Supabase Auth + PyJWT | Accounts and bearer-token sessions |
| Web search | Tavily | Real-time web results |
| PDF processing | pypdf | Text extraction from PDFs |

---

## 5. Prerequisites

- **Python 3.11** — the pinned dependencies require this version. Newer Python releases break the pinned `chroma-hnswlib` and LangChain builds.
- **Git** — to clone the repository (optional).
- **Free API accounts:**
  - [Groq](https://console.groq.com) — `GROQ_API_KEY`
  - [Supabase](https://supabase.com) — `SUPABASE_URL` and `SUPABASE_KEY`
  - [Tavily](https://tavily.com) — `TAVILY_API_KEY`
  - [OpenAI](https://platform.openai.com) — optional, used only as a fallback LLM

---

## 6. Installation and Setup

### 6.1 Clone the repository

```bash
git clone https://github.com/sankaruma8/LLMOPS_MULTI_AGENT_PLATFORM.git
cd LLMOPS_MULTI_AGENT_PLATFORM
```

### 6.2 Create a virtual environment and install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS / Linux

pip install -r requirements.txt
```

### 6.3 Create the environment file

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
```

---

## 7. Configuration

All configuration is read from environment variables, typically defined in `.env`.

### 7.1 Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Primary LLM provider key |
| `OPENAI_API_KEY` | Optional | Fallback LLM provider key |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon (public) key |
| `TAVILY_API_KEY` | Yes | Web search provider key |
| `SECRET_KEY` | Yes | Random string used to sign JWTs |
| `APP_ENV` | No | `development` (default) or `production` |

### 7.2 Supabase database schema

Create the following tables in Supabase:

```sql
-- users
create table users (
  id uuid primary key,
  email text,
  full_name text,
  created_at timestamptz,
  last_login timestamptz
);

-- chat_history
create table chat_history (
  id bigserial primary key,
  session_id text,
  role text,
  message text,
  created_at timestamptz default now()
);

-- documents
create table documents (
  id uuid primary key default gen_random_uuid(),
  filename text,
  file_hash text,
  session_id text,
  chunk_count int,
  version int,
  file_size bigint,
  page_count int,
  upload_date timestamptz
);
```

Enable **Authentication → Sign In / Up → Email** in the Supabase dashboard for signup and login to work.

> **Important:** `.env` is listed in `.gitignore` and must never be committed. The repository contains only the `.env.example` template.

---

## 8. Running the Application

Run the backend and frontend in two separate terminals.

**Terminal 1 — backend API:**

```bash
uvicorn app.main:app --reload --port 8000
# alternative: python run.py
```

**Terminal 2 — frontend UI:**

```bash
streamlit run frontend/app.py
```

| Resource | URL |
|----------|-----|
| Frontend | http://localhost:8501 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

---

## 9. Testing

The project includes a small smoke-test suite that verifies the workflow compiles and the planner behaves correctly.

```bash
pytest tests -q
```

Coverage:
- Graph compilation (`graph/` imports and compiles without error).
- Planner regex fast-path (greetings route to `CHAT`).
- Planner keyword fallback (web/chat/rag keywords route correctly).
- Planner always returns a valid route.

---

## 10. API Reference

Base URL: `http://localhost:8000`. Interactive documentation is generated at `/docs`.

### 10.1 System

#### `GET /`
Service information and endpoint map.

#### `GET /health`
Checks database connectivity.

```json
{ "status": "healthy", "database": "connected", "environment": "development" }
```

If the database is unreachable, `status` is `"unhealthy"` and `database` contains the error message.

### 10.2 Authentication

All auth requests accept/return JSON. Protected routes expect `Authorization: Bearer <token>`.

#### `POST /auth/signup`
Create an account.

```json
{
  "email": "user@example.com",
  "password": "secret123",
  "full_name": "Jane Doe"
}
```

**200 OK:**
```json
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user": { "id": "...", "email": "user@example.com", "full_name": "Jane Doe" },
    "access_token": "<jwt>",
    "token_type": "bearer"
  }
}
```

Errors: `409` if the email is already registered; `500` for other failures.

#### `POST /auth/login`
Body: `{ "email": "...", "password": "..." }`

**200 OK:** returns `access_token`, `refresh_token`, `token_type`, `expires_in`, and the user object.

#### `POST /auth/refresh`
Body: `{ "refresh_token": "..." }`

**200 OK:** returns fresh `access_token` and `refresh_token`.

#### `POST /auth/logout`
Header: `Authorization: Bearer <token>`

**200 OK:** `{ "success": true, "message": "Logged out successfully" }`

#### `GET /auth/me`
Header: `Authorization: Bearer <token>`

**200 OK:** user object with `id`, `email`, `full_name`, `created_at`, `last_login`.

#### `PUT /auth/profile?full_name=New Name`
Header: `Authorization: Bearer <token>`

**200 OK:** `{ "success": true, "message": "Profile updated successfully" }`

### 10.3 Chat

#### `POST /chat`
Send a message. The system routes it automatically to Chat, RAG, or Web.

```json
{ "session_id": "streamlit_123", "message": "What is a transformer?", "stream": false }
```

**200 OK:**
```json
{
  "success": true,
  "message": "Response generated successfully",
  "data": {
    "agent": "RAG",
    "answer": "A transformer is a neural network architecture ...",
    "latency_ms": 1842.11,
    "user": "anonymous"
  }
}
```

`user` is the authenticated user's email, or `"anonymous"` when no token is supplied.

#### `POST /chat/stream`
Same body; returns a `text/event-stream`:

```
data: {"type": "start", "agent": "RAG"}
data: {"type": "chunk", "content": "A transformer is "}
data: {"type": "end", "answer": "..."}
```

#### `GET /history/{session_id}`
Returns the conversation history for a session.

### 10.4 Documents

#### `POST /upload`
Upload a PDF (multipart form). Field: `file` (required), `session_id` (optional).

**200 OK (new upload):**
```json
{
  "success": true,
  "message": "PDF uploaded and indexed",
  "data": { "status": "new", "filename": "notes.pdf", "version": 1,
            "chunks": 73, "pages": 26, "file_size": 1363148, "doc_id": "..." }
}
```

**200 OK (duplicate):** `data.status` is `"duplicate"` and `data.existing_document` is returned.

Errors: `400` for non-PDF files or PDFs with no extractable text.

#### `POST /upload/batch`
Multiple PDFs; returns per-file results and totals.

#### `GET /upload/list?session_id=...`
List documents.

#### `GET /documents`
Alias for listing with a nested `documents` array.

#### `GET /documents/stats`
Storage and vector statistics.

#### `GET /documents/{filename}/history`
Version history for a document.

#### `DELETE /documents/{filename}`
Deletes document chunks and metadata.

---

## 11. User Guide

### 11.1 Dashboard

The home page shows two cards:

- **Chat** — ask anything; the system routes to the best agent automatically.
- **Documents** — upload PDFs to build the RAG knowledge base.

### 11.2 Chatting

1. Open the **Chat** page.
2. Type a question.
3. The answer appears with the routing agent and latency noted beneath it.

| Route | Used for | Examples |
|-------|----------|----------|
| **Chat** | Greetings, small talk, general knowledge | "hello", "what is your opinion?" |
| **RAG** | Questions about uploaded documents | "summarise page 3 of my notes" |
| **Web** | Current or real-time information | "latest AI news", "weather today" |

If the first agent's answer is weak, the system automatically retries via the other source.

### 11.3 Managing documents

1. Open the **Documents** page.
2. Upload one or more PDFs.
3. View processed documents with chunk/page/version/size details.
4. Re-uploading the same file is detected and skipped (duplicate notice).

---

## 12. Deployment

### 12.1 Docker

The repository includes `Dockerfile` (API) and `Dockerfile.frontend` (UI).

```bash
docker build -t llmops-api .
docker run -p 8000:8000 --env-file .env llmops-api
```

### 12.2 Render

`render.yaml` defines two web services — `llmops-api` and `llmops-frontend` — using Docker.

- Environment variables are declared with `sync: false` so their values are entered in the Render dashboard and never stored in the repository.
- `SECRET_KEY` is generated automatically with `generateValue: true`.
- Note: ChromaDB is local to the container filesystem; uploaded documents are not shared across deploys unless persistent storage is attached.

---

## 13. Security Considerations

- **Never commit `.env`.** It contains provider API keys.
- **Set a strong `SECRET_KEY`** in any shared environment; the default is a placeholder.
- **Use the Supabase anon key**, never the service-role key, in this application.
- **CORS** currently allows all origins (`allow_origins=["*"]`). For a public deployment, restrict it to the frontend origin.
- **Uploads** are stored on the local disk. In a shared deployment, enforce file-size limits and access control.
- The repository is public; the `.env.example` contains only placeholder values.

See `SECURITY.md` for the full policy.

---

## 14. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| "Both LLM providers are currently unavailable" | Missing or invalid `GROQ_API_KEY` / `OPENAI_API_KEY` | Update keys in `.env` and restart the backend |
| `/health` reports `unhealthy` | Missing or placeholder `SUPABASE_URL` / `SUPABASE_KEY` | Set real Supabase credentials |
| "Only PDF files are allowed" | Non-PDF upload | Upload a `.pdf` file |
| "PDF may be image-based or scanned" | PDF has no extractable text layer | Use a text-based PDF |
| Frontend shows "API: Offline" | Backend not running, or wrong `BACKEND_URL` | Start the backend; check `BACKEND_URL` |
| `pip install` fails on `chroma-hnswlib` | Wrong Python version | Use Python 3.11 |

---

## 15. Project Structure

```
agents/          planner, response, retriever, web, validator agents
api/             FastAPI routers (auth, upload)
app/             FastAPI app, configuration, JWT dependencies
database/        Supabase client, document metadata manager
docs/            project documentation (this and related guides)
frontend/        Streamlit UI (app + pages)
graph/           LangGraph state machine (state, nodes, workflow)
memory/          conversation history manager
prompts/         system prompts and prompt builders
rag/             document loading, chunking, embeddings, vector store, retriever
tests/           unit tests
```

Key entry points:

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application and endpoints |
| `graph/workflow.py` | LangGraph workflow definition |
| `graph/nodes.py` | Agent node implementations |
| `agents/planner_agent.py` | Intent classification |
| `frontend/app.py` | Streamlit dashboard |
| `run.py` | Convenience backend launcher |

---

## 16. Conclusion

The LLMOps Multi-Agent Platform demonstrates how prompt refinement and multi-agent orchestration improve the reliability and grounding of generative AI responses. By classifying intent, routing to specialist agents, injecting context, validating output quality, and retrying through alternative sources, the system produces more accurate and contextual answers than a single generic LLM call. Its modular, graph-based design keeps the workflow deterministic and bounded, and makes the platform easy to extend with additional agents in the future.
