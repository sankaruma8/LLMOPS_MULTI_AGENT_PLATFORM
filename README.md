# LLMOps Multi-Agent Platform

A college project that refines a user's raw prompt into a structured task and routes it to the right specialist agent — **Chat**, **RAG** (document Q&A), or **Web Search** — using a LangGraph state machine with automatic validation and fallback.

## Features

- **Multi-agent orchestration** — a LangGraph DAG routes each question to Chat, RAG, or Web, validates the answer, and retries through the other sources if the answer is weak.
- **RAG** — upload PDFs, they are chunked, embedded with Sentence-Transformers (`all-MiniLM-L6-v2`), and stored in ChromaDB for semantic retrieval.
- **Web search** — live answers with citations via Tavily.
- **Conversation memory** — chat history is persisted in Supabase and injected as context (sliding window).
- **Auth** — JWT auth backed by Supabase Auth.
- **Frontend** — Streamlit dashboard (chat + document management).

## Architecture

```
Streamlit (frontend) ──► FastAPI ──► LangGraph workflow
                                        │
                    ┌───────────────┬───┴───────────────┐
                    ▼               ▼                   ▼
                  CHAT            RAG                WEB
                    └───────────────┴───────────────────┘
                                        │
                                        ▼
                                   VALIDATOR ──(retry RAG/WEB)──► SAVE ──► Supabase
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| API | FastAPI + Uvicorn |
| LLM | Groq (Llama 3.3) with OpenAI (GPT-4o) fallback |
| Orchestration | LangGraph |
| RAG | ChromaDB + Sentence-Transformers |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth + JWT |
| Web Search | Tavily |

## Getting Started

### Prerequisites
- Python 3.11 (the pinned dependencies require 3.11)

### Setup
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt

copy .env.example .env        # then fill in your API keys
```

Required keys in `.env`:
- `GROQ_API_KEY` — primary LLM (https://console.groq.com)
- `OPENAI_API_KEY` — fallback LLM (optional)
- `SUPABASE_URL` + `SUPABASE_KEY` — Postgres + auth (https://supabase.com)
- `TAVILY_API_KEY` — web search (https://tavily.com)
- `SECRET_KEY` — random string used to sign JWTs

### Run
```bash
# Backend
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
streamlit run frontend/app.py

# Tests
pytest tests -q
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Create account |
| POST | `/auth/login` | Login, get JWT |
| POST | `/auth/logout` | Logout |
| GET | `/auth/me` | Current user |
| POST | `/chat` | Send a message (auto-routed) |
| POST | `/chat/stream` | Streamed chat response |
| POST | `/upload` | Upload a PDF for RAG |
| GET | `/upload/list` | List uploaded documents |
| GET | `/history/{session_id}` | Conversation history |
| GET | `/health` | Health check |

Interactive docs at `http://localhost:8000/docs`.

## Project Structure

```
agents/          planner, chat response, RAG retriever, web search, validator
api/             FastAPI routers (auth, upload)
app/             FastAPI app, config, auth dependencies
database/        Supabase client, document metadata manager
graph/           LangGraph state machine (nodes, workflow, state)
memory/          conversation history manager
prompts/         system prompts and prompt builders
rag/             document loading, chunking, embeddings, vector store
frontend/        Streamlit UI
docs/            project documentation
tests/           unit tests
```

## Documentation

| Document | Contents |
|----------|----------|
| [DOCUMENTATION.md](DOCUMENTATION.md) | Complete single-file documentation (intro → architecture → setup → API → deploy) |
| [docs/setup.md](docs/setup.md) | Installation, environment, Supabase tables, running locally, deploy |
| [docs/architecture.md](docs/architecture.md) | System design, components, data flow |
| [docs/api_reference.md](docs/api_reference.md) | Endpoint-by-endpoint API reference |
| [docs/user_guide.md](docs/user_guide.md) | How to use the app + troubleshooting |
| [docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md) | College report (abstract, methodology, results) |
| [docs/algorithm_and_dataset.md](docs/algorithm_and_dataset.md) | Algorithm and dataset write-up |

## License

College project — not for production use.
