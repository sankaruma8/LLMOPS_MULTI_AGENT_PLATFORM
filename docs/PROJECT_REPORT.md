# Project Report

## LLMOps Multi-Agent Platform
### Refining Input Prompts to Effectively Guide Generative AI Models in Producing Desired Outputs

---

## 1. Abstract

Generative AI models are powerful, but the quality of their output depends heavily on how the input prompt is framed. This project presents a **multi-agent platform** that automatically refines a user's raw prompt into a structured task and dispatches it to the most suitable specialist agent. Built on a LangGraph state machine, the system classifies intent (Chat, document-based RAG, or live Web search), generates an answer with citations where applicable, validates the result, and automatically retries through other sources when the answer is weak. The result is a system that produces more accurate, grounded, and context-aware answers than a single generic prompt-to-model call.

## 2. Introduction

Large language models (LLMs) such as Llama and GPT can answer questions, summarise documents, and search the web — but no single call handles all of these well. A vague prompt may produce a generic answer when the user wanted document-grounded detail or live, up-to-date facts.

This project addresses that problem with an **orchestration layer**: instead of sending the raw prompt straight to one model, a planner first understands *what kind of answer the user needs*, then routes to a specialist agent that is given a refined, purpose-built prompt along with the right context (conversation history, uploaded documents, or web results). A validation step and a bounded fallback loop ensure that weak answers are caught and retried.

## 3. Objectives

1. Refine raw user prompts into structured, agent-specific tasks.
2. Route each task to the correct specialist agent: Chat, RAG (documents), or Web search.
3. Ground answers in evidence — document citations or source URLs — where applicable.
4. Maintain conversation context across turns using persistent memory.
5. Validate output quality and retry through alternative sources on failure.
6. Provide a simple web interface for chatting and document upload.

## 4. Scope

**Included:** conversational chat, PDF-based retrieval-augmented generation, live web search, conversation memory, JWT-authenticated accounts, document management (upload, versioning, duplicate detection), a Streamlit UI, and deployment configuration for Render.

**Not included (out of scope):** fine-tuning of models, multi-lingual support, and production-grade multi-tenant isolation.

## 5. Literature / Background

- **Prompt engineering** — the practice of crafting inputs to steer LLM outputs; the project applies this at a system level rather than manually.
- **Retrieval-Augmented Generation (RAG)** — grounding LLM answers in a retrieved corpus (Lewis et al., 2020) to reduce hallucination and cite sources.
- **Multi-agent orchestration** — decomposing a task into specialist agents coordinated by a state machine (LangGraph).
- **Embeddings and vector search** — semantic retrieval via `all-MiniLM-L6-v2` (Sentence-Transformers) and ChromaDB.

## 6. Methodology

The platform is built as a **Directed Acyclic Graph** (LangGraph `StateGraph`) with a shared `AgentState`. Each node is an agent function.

**Workflow:** `MEMORY → PLANNER → {CHAT | RAG | WEB} → VALIDATOR → SAVE`

1. **Memory node** loads the last N turns from Supabase (sliding window) and lists uploaded documents from ChromaDB.
2. **Planner node** classifies the question:
   - Fast regex path for greetings → `CHAT` (no LLM cost).
   - Otherwise an LLM call constrained to `{CHAT, RAG, WEB}`, defaulting to `RAG` on invalid output.
   - Keyword fallback if the LLM is unavailable.
3. **Agent nodes** build a refined prompt with their own system prompt plus injected context:
   - *Chat* — general knowledge + history + list of available documents.
   - *RAG* — top-8 chunks retrieved by cosine similarity, answered with document/page citations.
   - *Web* — Tavily search results, answered with source URLs.
4. **Validator node** rejects empty, too-short, or failure-phrase answers (e.g. "sorry, I couldn't find").
5. **Fallback loop** — on failure, the system retries the other source (RAG ↔ WEB, max 2 retries) before saving gracefully.
6. **Save node** persists the conversation turn to Supabase.

**Prompt refinement is the core contribution:** every stage re-interprets the raw prompt through a purpose-built system prompt, injecting memory and source context so the model can produce grounded, desired outputs.

## 7. System Architecture

```
Streamlit (frontend)
      │  HTTP / JSON
      ▼
FastAPI  ──►  LangGraph workflow
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
    CHAT         RAG          WEB
      │            │            │
      └────────────┴────────────┘
                   │
                   ▼
              VALIDATOR ──(retry RAG/WEB)──► SAVE ──► Supabase
                   │
                   ▼
            ChromaDB (chunks) / Tavily / Groq / OpenAI
```

**Technology stack:**

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| API | FastAPI + Uvicorn |
| Orchestration | LangGraph |
| LLM | Groq (Llama 3.3) with OpenAI (GPT-4o) fallback |
| Embeddings | Sentence-Transformers `all-MiniLM-L6-v2` |
| Vector store | ChromaDB |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth + JWT |
| Web search | Tavily |
| PDF processing | pypdf |

## 8. Implementation

Key modules:

- `graph/` — the state machine: `state.py` (schema), `nodes.py` (agent functions), `workflow.py` (edges + routing + fallback).
- `agents/` — `planner_agent.py` (intent), `response_agent.py` (LLM wrapper with fallback), `retriever_agent.py`, `web_agent.py`, `validator_agent.py`.
- `rag/` — `document_loader.py`, `text_splitter.py` (~500 chars, 50 overlap), `embeddings.py`, `vector_store.py`, `retriever.py`.
- `memory/` — Supabase-backed sliding-window conversation memory.
- `api/` — FastAPI routers: `auth.py`, `upload.py`.
- `app/` — FastAPI app, configuration, JWT dependencies.
- `frontend/` — Streamlit pages: Chat, Documents.

**Notable implementation details:**
- Duplicate upload detection via SHA-256 file hashing.
- Graceful degradation — an unavailable database or LLM never crashes a request.
- Bounded orchestration — worst case is fixed (one pass per source, max two retries).

## 9. Results and Evaluation

Automated tests (`tests/test_core.py`): graph compilation, planner fast-path, fallback routing — all passing.

Observed routing outcomes:

| Input | Route | Result |
|-------|-------|--------|
| "hello" | CHAT | Greeting answered via regex fast-path (no LLM call) |
| "what is transformers in AI" (with notes uploaded) | RAG | Answered from `genai_notes.pdf` with citations |
| "what is the latest news today" | WEB | Live answer with source URLs |
| Weak/failed RAG answer | → WEB | Validator triggered automatic retry |

Latency is dominated by LLM inference (~1–2 s per call); the regex fast-path avoids the LLM for greetings, and the fallback loop is bounded so worst-case latency is predictable.

## 10. Limitations

- RAG quality depends on uploaded documents having an extractable text layer (scanned PDFs are not supported).
- ChromaDB is local storage — on serverless deploys, uploaded documents do not persist across restarts without attached storage.
- Intent classification can be imperfect for ambiguous or compound questions.
- English-only prompts.

## 11. Future Work

- Support for scanned/image PDFs via OCR.
- Streaming token-by-token output through the UI.
- Persistent vector storage (e.g. Supabase pgvector) for cloud deployments.
- Additional specialist agents (math/calculation, code, summarisation).
- Conversation summarisation for long sessions beyond the sliding window.

## 12. Conclusion

The project demonstrates how prompt refinement and multi-agent orchestration improve the usefulness of generative AI. By classifying intent, routing to specialist agents, grounding answers in documents or the live web, and validating output quality with automatic retry, the platform produces more accurate and contextual answers than a single generic LLM call. The modular graph-based design makes it straightforward to add new agents in the future.

## 13. References

1. LangGraph documentation — https://langchain-ai.github.io/langgraph/
2. Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.*
3. Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.*
4. ChromaDB documentation — https://docs.trychroma.com/
5. Tavily API documentation — https://docs.tavily.com/
6. Supabase documentation — https://supabase.com/docs
