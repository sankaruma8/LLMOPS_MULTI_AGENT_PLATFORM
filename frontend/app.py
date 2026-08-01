import os
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="LLMOps Multi-Agent Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Links")
st.sidebar.markdown(f"[API Docs]({BACKEND_URL}/docs)")

st.sidebar.markdown("---")
st.sidebar.markdown("### System Info")
try:
    from api import api_get_sync
    health = api_get_sync("/health")
    if health.get("status") == "healthy":
        st.sidebar.success("API: Healthy")
    else:
        st.sidebar.warning("API: Degraded")
except Exception:
    st.sidebar.error("API: Offline")

st.sidebar.markdown("---")
st.sidebar.caption("LLMOps v1.0 | College Project")

st.title("🤖 LLMOps Multi-Agent Platform")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💬 Chat")
    st.markdown("Ask questions, get answers from RAG, web search, or general chat.")
    st.page_link("pages/01_chat.py", label="Open Chat", icon="💬")

with col2:
    st.markdown("### 📄 Documents")
    st.markdown("Upload PDFs for RAG-powered document Q&A.")
    st.page_link("pages/02_documents.py", label="Manage Documents", icon="📄")

st.markdown("---")

st.markdown("### Architecture")
st.markdown("""
| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit |
| **API** | FastAPI + Uvicorn |
| **LLM** | Groq (Llama 3.3) + OpenAI (GPT-4o fallback) |
| **Agents** | LangGraph (3-route routing) |
| **RAG** | ChromaDB + Sentence-Transformers |
| **Database** | Supabase PostgreSQL |
| **Auth** | Supabase Auth + JWT |
""")
