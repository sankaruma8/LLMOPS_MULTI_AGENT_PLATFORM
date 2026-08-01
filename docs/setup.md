# Setup Guide

## Prerequisites

- **Python 3.11** — the pinned dependencies require Python 3.11 (newer versions break `chroma-hnswlib`/langchain builds).
- **Git** (optional, to clone).
- Accounts for: [Groq](https://console.groq.com), [Supabase](https://supabase.com), [Tavily](https://tavily.com). OpenAI is optional (fallback LLM).

## 1. Clone and install

```bash
git clone https://github.com/sankaruma8/LLMOPS_MULTI_AGENT_PLATFORM.git
cd LLMOPS_MULTI_AGENT_PLATFORM

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS / Linux

pip install -r requirements.txt
```

## 2. Configure environment

Copy the template and fill in your keys:

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
```

Edit `.env`:

```ini
GROQ_API_KEY=gsk_your_groq_key_here      # primary LLM (Llama 3.3)
OPENAI_API_KEY=sk-your_openai_key_here   # optional fallback LLM (GPT-4o)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SECRET_KEY=your_random_secret_key        # used to sign JWTs - use a long random string
TAVILY_API_KEY=tvly-your_tavily_key
APP_ENV=development
```

**Note:** `.env` is git-ignored. Never commit it.

### Supabase setup

The app expects three tables:

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

Enable **Auth > Email/Password** in the Supabase dashboard for signup/login to work.

## 3. Run locally

Terminal 1 — backend:

```bash
uvicorn app.main:app --reload --port 8000
# or: python run.py
```

Terminal 2 — frontend:

```bash
streamlit run frontend/app.py
```

Open:
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 4. Run tests

```bash
pytest tests -q
```

## 5. Docker / Render deployment

The repo ships `Dockerfile` (API) and `Dockerfile.frontend` (UI), plus `render.yaml` for Render. The API image:

```bash
docker build -t llmops-api .
docker run -p 8000:8000 --env-file .env llmops-api
```

On Render, `render.yaml` deploys the API and frontend as two web services. Set the env vars there (keys use `sync: false` so they are entered in the dashboard, never stored in the repo).
