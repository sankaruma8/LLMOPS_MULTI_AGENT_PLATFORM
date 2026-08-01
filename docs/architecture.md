# Architecture

## Overview

The platform is a **prompt-refinement and multi-agent orchestration system**. A raw user question is classified by an LLM-based planner, routed to the correct specialist agent (Chat / RAG / Web), validated, and automatically retried through other sources if the answer is weak.

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
      │                                                      │ retry
      ▼                                                      └────────┘
  Supabase (history, users, docs)        ChromaDB (chunks)        Tavily / Groq / OpenAI
```

## Components

### 1. Backend API (`app/`, `api/`)

- **`app/main.py`** — FastAPI app. Registers routers, CORS, startup model warm-up, and endpoints:
  - `POST /chat`, `POST /chat/stream`
  - `GET /history/{session_id}`
  - `GET /health`, `GET /`
- **`app/config.py`** — reads all settings from environment variables.
- **`app/dependencies.py`** — JWT verification helpers used as FastAPI dependencies.
- **`api/auth.py`** — Supabase Auth wrapper: signup, login, refresh, logout, me, profile.
- **`api/upload.py`** — PDF upload, duplicate detection, chunking, embedding, indexing.

### 2. LangGraph orchestration (`graph/`)

A `StateGraph` over `AgentState` (see `graph/state.py`). Nodes in `graph/nodes.py`:

| Node | Responsibility |
|------|----------------|
| `memory` | Loads conversation history from Supabase (sliding window), lists available documents from ChromaDB |
| `planner` | Classifies intent → `CHAT` / `RAG` / `WEB` (regex fast-path + LLM fallback) |
| `chat` | Answers from general knowledge, injecting history + available docs |
| `rag` | Retrieves relevant chunks from ChromaDB, answers with citations |
| `web` | Searches Tavily, answers with source URLs |
| `validator` | Quality gate: rejects empty/short answers and failure phrases |
| `save` | Persists the user question + assistant answer to Supabase |

**Fallback loop:** if the validator rejects an answer, the workflow retries the other sources (`RAG` ↔ `WEB`) before giving up gracefully. Worst case is bounded (max 2 retries).

### 3. Agents (`agents/`)

- **`planner_agent.py`** — intent classification. Fast regex path for greetings; otherwise an LLM call constrained to one of 3 labels; keyword fallback if the LLM errors.
- **`response_agent.py`** — single LLM call wrapper. Uses Groq (`llama-3.3-70b-versatile`) with automatic OpenAI (`gpt-4o`) fallback.
- **`retriever_agent.py`** — embeds the question and retrieves the top-k chunks from the vector store.
- **`web_agent.py`** — Tavily search + result formatting.
- **`validator_agent.py`** — string-based answer validation (length + failure phrases).

### 4. RAG pipeline (`rag/`)

```
PDF upload → pypdf extraction (document_loader.py)
           → chunking, ~500 chars / 50 overlap (text_splitter.py)
           → embeddings, all-MiniLM-L6-v2, 384-dim (embeddings.py)
           → ChromaDB persistent store (vector_store.py)
Query → embed → cosine-similarity search (retriever.py) → top 8 chunks
```

### 5. Memory (`memory/`)

- `memory_manager.py` reads/writes `chat_history` in Supabase and returns a sliding window (last 20 messages) for prompt context.

### 6. Database (`database/`)

- `supabase_client.py` — lazy singleton Supabase client.
- `document_manager.py` — document metadata: duplicate detection (SHA-256), versioning, listing.

### 7. Frontend (`frontend/`)

Streamlit multi-page app (`frontend/app.py` + `pages/`). Calls the backend through `frontend/api.py` helpers. Pages: Chat, Documents.

## Key design decisions

- **Prompt refinement is the core idea** — the planner turns a raw prompt into a structured task; each agent re-interprets the prompt through its own system prompt with memory + source context injected.
- **Graceful degradation** — DB or LLM unavailability never crashes a request; the graph logs and falls back to a graceful message.
- **Bounded orchestration** — the graph is a DAG with a max 2-retry fallback loop, so latency is predictable.

## Data flow for a request

1. `POST /chat` with `{session_id, message}`.
2. `memory_node` loads history + doc list.
3. `planner_node` picks a route.
4. The chosen agent builds a refined prompt and generates an answer.
5. `validator_node` checks quality → retries via the other source if needed.
6. `save_node` persists the turn.
7. Response: `{agent, answer, latency_ms, user}`.
