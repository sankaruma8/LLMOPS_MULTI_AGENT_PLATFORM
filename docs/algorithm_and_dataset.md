# ALGORITHM AND DATASET

## Project: LLMOps Multi-Agent Platform — Refine input prompts to effectively guide generative AI models in producing desired outputs

The project is a **prompt-refinement and multi-agent orchestration system**. A user question (raw prompt) is automatically classified by an LLM-based planner into a route, dispatched to the matching specialist agent (CHAT / RAG / WEB), executed, validated, and — if the answer fails validation — automatically retried through the other sources until a quality answer is produced.

---

## 1. SYSTEM ARCHITECTURE

The system is built as a **Directed Acyclic Graph (DAG)** using LangGraph's StateGraph. Each node is an agent function that reads and updates a shared `AgentState`. The state machine guarantees deterministic execution and enables the fallback loop.

```
START
  │
  ▼
MEMORY ──► PLANNER ──► [conditional branch by route]
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
            CHAT         RAG         WEB
              │           │           │
              └───────────┴───────────┘
                          │
                          ▼
                      VALIDATOR
                          │  valid? ── yes ──► SAVE ──► END
                          │
                          │  no ── (retry RAG or WEB, max once each)
                          ▼
                   escalate route and retry
```

---

## 2. MAIN ALGORITHM — Multi-Agent Orchestration

### 2.1 Inputs
- `question` (string) — raw user prompt
- `session_id` (string) — conversation identifier for memory

### 2.2 Step-by-Step Procedure

**Step 1 — MEMORY NODE (context loading)**
- Load the last N conversation messages for `session_id` from Supabase memory (sliding window).
- Query ChromaDB for the list of available uploaded documents.
- Initialise empty slots: `rag_context = ""`, `web_context = ""`, `routes_tried = []`.
- **Outputs:** enriched `AgentState` with history and document availability.

**Step 2 — PLANNER NODE (prompt refinement / intent classification)**
- Apply a regex **fast-path check** (condition): greeting pattern (hi / hello / thanks / bye ...) → route = `CHAT`.
- Otherwise call the LLM planner with the instruction prompt `PLANNER_SYSTEM_PROMPT`, appending the last few conversation turns as context.
- Parse the model output and verify it is one of `{CHAT, RAG, WEB}`; invalid outputs default to `RAG`.
- **Fallback condition:** if the LLM call throws an exception → use keyword-based `_fallback_planner()`.
- **Outputs:** `route` (string) — the refined intent label.

**Step 3 — CONDITIONAL BRANCH (routing)**
- `route == "CHAT"` → chat_node
- `route == "RAG"` → rag_node
- `route == "WEB"` → web_node

**Step 4 — AGENT EXECUTION**

*CHAT Agent*
- Build a refined prompt via `build_chat_prompt()` which injects the user question, conversation history, and the list of available documents (so the model knows what sources exist).
- Generate the answer with the LLM.
- **Outputs:** `answer`, `sources = []`, push `"CHAT"` to `routes_tried`.

*RAG Agent* (Retrieval-Augmented Generation)
- Embed the question using the Sentence-Transformer embedder (`all-MiniLM-L6-v2`).
- Retrieve top **k = 8** chunks from the ChromaDB vector store by cosine similarity.
- **Condition:** if chunks exist → build a document context via `format_context()`, and generate an answer from the refined hybrid prompt (`build_hybrid_prompt` with `rag_context`). If no chunks → empty answer (triggers fallback).
- **Outputs:** `answer`, `sources` (document names + page numbers), push `"RAG"` to `routes_tried`.

*WEB Agent*
- Call the Tavily web-search API with the question.
- **Condition:** if results exist → format them into a web context, generate an answer citing source URLs. Else empty answer.
- **Outputs:** `answer`, `sources` (top 3 URLs), push `"WEB"` to `routes_tried`.

**Step 5 — VALIDATOR NODE (quality gate)**
- **Conditions for valid:**
  1. answer is not empty and `len(answer.strip()) >= 10`, AND
  2. answer contains **none** of the `FAILURE_PHRASES` (e.g. "i couldn't find", "sorry", "not available", ...).
- **Outputs:** `valid` (boolean).

**Step 6 — FALLBACK LOOP (escalation)**
- **If valid** → go to SAVE.
- **If invalid**, decide the next attempt by conditions on `routes_tried`:
  1. `"RAG"` tried and `"WEB"` not tried → retry with `WEB`
  2. `"WEB"` tried and `"RAG"` not tried → retry with `RAG`
  3. otherwise → SAVE (give up gracefully)
- **Loop termination condition:** the loop runs at most 2 retries (RAG ↔ WEB), guaranteeing a bounded worst-case execution.

**Step 7 — SAVE NODE (persistence)**
- **Condition:** if `answer` is non-empty → save `{role: user, message: question}` and `{role: assistant, message: answer}` to Supabase with the `session_id`.

### 2.3 Final Output
JSON response to the client containing:
- `answer` (string)
- `agent` / `route` (string) — which agent produced the answer
- `sources` (list) — document names / URLs
- `latency_ms` (float) — measured end-to-end latency

---

## 3. KEY SUB-ALGORITHMS

### 3.1 Prompt-Refinement (Planner) — the project's core contribution

Input: raw user question. Output: a refined route label.

1. Normalise to lowercase, strip whitespace.
2. **Fast-path regex** (no LLM cost): greeting → CHAT.
3. **LLM classification** with a strict instruction prompt (few-shot, constrained output) — returns exactly one of 3 labels.
4. **Validation condition:** label must be in the allowed set, else default RAG.
5. **Failure condition:** exception → keyword fallback classifier.

The same principle refines prompts at generation time: system prompts for each agent instruct *how* the raw prompt should be interpreted, memory is injected to keep context, and document names are injected so the model can decide whether to cite uploaded content.

### 3.2 Retrieval-Augmented Generation (RAG)

1. Split uploaded PDFs into text chunks (recursive text splitter, ~500 chars with 50 overlap).
2. Embed each chunk with Sentence-Transformer (`all-MiniLM-L6-v2`, 384-dim).
3. Store in ChromaDB with metadata (filename, page).
4. At query time: embed the question, cosine-similarity search, take top 8 chunks.
5. Build refined prompt + generate answer with citations.

---

## 4. REQUIRED LIBRARIES

**Core / Framework**
| Library | Purpose |
|---------|---------|
| `fastapi` | Backend REST API |
| `uvicorn` | ASGI server |
| `langgraph` | Orchestration state graph (workflow, conditional edges) |
| `pydantic` | Data validation / request models |

**AI / LLM**
| Library | Purpose |
|---------|---------|
| `groq` | Primary LLM inference (Llama 3.3) |
| `openai` | Fallback LLM (GPT-4o) |
| `sentence-transformers` | Embedding model `all-MiniLM-L6-v2` |

**RAG / Storage**
| Library | Purpose |
|---------|---------|
| `chromadb` | Vector database for document chunks |
| `pypdf` | PDF text extraction |
| `supabase` | PostgreSQL (chat history, users, documents) |

**Web Search**
| Library | Purpose |
|---------|---------|
| `tavily-python` | Real-time web search |

**Frontend**
| Library | Purpose |
|---------|---------|
| `streamlit` | Chat / Documents UI |
| `httpx` | HTTP calls (backend + frontend) |

**Deployment / Security**
| Library | Purpose |
|---------|---------|
| `python-dotenv` | Environment variables |
| `pyjwt` | JWT authentication |

---

## 5. DATASETS USED

This is an LLM + RAG system, so it uses **both a pre-trained model dataset (implicit) and a user-supplied document corpus (explicit)**.

### 5.1 Pretrained Model Datasets (implicit)
| Dataset / Model | Provider | Size | Use |
|-----------------|----------|------|-----|
| `Llama-3.3-70B` (via Groq) | Meta / Groq | 70B params | Intent classification, answer generation |
| `GPT-4o` (fallback) | OpenAI | — | Backup LLM if Groq unavailable |
| `all-MiniLM-L6-v2` | SBERT | 384-dim embeddings | Semantic search / retrieval |
| `MS MARCO` / `SNLI` pretraining | SBERT | — | Training corpus behind the embedding model |

### 5.2 User-Document Corpus (explicit RAG dataset)
The system's retrieval corpus is built from user-uploaded PDFs. For this project, academic notes were uploaded and indexed into ChromaDB, e.g. `genai_notes.pdf` (26 pages, 73 chunks), `Machine_Learning_Notes.pdf`, `CN UNIT-II.pdf`, and other course material.

Each uploaded document is processed by the pipeline:
1. **Input:** raw PDF file.
2. **Step 1:** extract raw text with `pypdf` (page by page).
3. **Step 2:** split into overlapping chunks (~500 characters, 50 overlap).
4. **Step 3:** embed each chunk with `all-MiniLM-L6-v2`.
5. **Step 4:** insert into ChromaDB with metadata `{filename, page}`.
6. **Output:** queryable vector collection (returned with cosine-similarity search at query time).

### 5.3 Runtime Datasets (generated)
| Dataset | Source | Use |
|---------|--------|-----|
| Conversation history | Supabase table | Memory injection into prompts |
| Web search results | Tavily API | Up-to-date factual grounding |

---

## 6. ALGORITHM COMPLEXITY

- **Planner fast-path:** O(n) regex scan of the query.
- **Retrieval:** approximate nearest-neighbour search in ChromaDB (HNSW), effectively O(log N) on the document corpus (thousands of chunks).
- **Workflow:** bounded — every node executes exactly once except the fallback loop, which terminates after at most 2 retries, giving worst-case **O(nodes) ≈ 9 node executions** (constant time complexity).
- **LLM inference:** dominates latency (~1–2 s per generation call); mitigated by the regex fast-path which skips the LLM planner for greetings.

---

## 7. VALIDATION RESULTS

| Test Suite | Cases | Result |
|------------|-------|--------|
| Core smoke tests (graph compiles, planner fast-path, fallback routing) | 4 | ✅ All passed |

Example route outcomes observed:
- `"hello"` → CHAT (regex fast-path, no LLM cost)
- `"what is transformers in AI"` (with docs) → RAG (answered from `genai_notes.pdf`)
- `"what is latest news today"` → WEB
- A question that fails RAG validation → retried via WEB, or vice versa
