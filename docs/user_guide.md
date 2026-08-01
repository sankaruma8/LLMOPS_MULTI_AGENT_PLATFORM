# User Guide

## Starting the app

Make sure the backend and frontend are both running (see [setup.md](setup.md)).

1. Backend: `uvicorn app.main:app --reload --port 8000`
2. Frontend: `streamlit run frontend/app.py`

Open **http://localhost:8501**.

## Dashboard

The home page shows two cards:

- **Chat** — ask anything; the system routes to the best agent automatically.
- **Documents** — upload PDFs to build your RAG knowledge base.

## Chatting

1. Open the **Chat** page.
2. Type a question in the input box.
3. Wait for the answer — the agent that answered and the latency are shown under the reply.

### How questions are routed

| Route | When it is used | Examples |
|-------|-----------------|----------|
| 💬 **Chat** | Greetings, small talk, general knowledge | "hello", "thanks", "what is your opinion?" |
| 📖 **RAG** | Questions about your uploaded documents | "what is on page 3 of my notes?" |
| 🔍 **Web** | Current / real-time information | "latest AI news", "weather today" |

If the first agent produces a weak answer (empty or generic), the system automatically retries the other source before giving up.

### Tips
- Upload documents *first* for accurate RAG answers — the model can then answer from your files.
- Start a fresh session with **Clear Chat** to reset context.

## Managing documents

1. Open the **Documents** page.
2. **Upload tab:** choose a PDF (or several for batch upload) and click upload.
3. Processing: text is extracted → chunked → embedded → indexed into ChromaDB. You'll see chunk/page/version counts.
4. **Documents tab:** browse everything uploaded, with chunk count, page count, version, size, and upload date.

**Duplicate handling:** uploading the same file again is detected (SHA-256) and skipped — you'll get a "duplicate" notice instead of duplicate indexing.

## Accounts

Signup and login are enabled if you configured Supabase Auth (email/password). Logged-in users' email is shown in chat responses; without a token requests still work as `anonymous`.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| "Both LLM providers are currently unavailable" | `GROQ_API_KEY` / `OPENAI_API_KEY` missing or invalid in `.env` |
| Health shows `unhealthy` | `SUPABASE_URL` / `SUPABASE_KEY` missing or placeholder |
| "Only PDF files are allowed" | Upload endpoint only accepts `.pdf` |
| "PDF may be image-based or scanned" | The PDF has no extractable text layer — use a text-based PDF |
| Frontend says "API: Offline" | Backend not running, or `BACKEND_URL` points at the wrong host |

## Deployment notes

- **Render:** `render.yaml` deploys the API and frontend as two web services. Enter secrets in the Render dashboard (keys are `sync: false`, never committed).
- **Data persistence:** ChromaDB is local (`./chroma_db`), so uploaded documents are not shared between Render deploys unless you attach persistent storage.
