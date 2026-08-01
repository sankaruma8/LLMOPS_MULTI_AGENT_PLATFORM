import os
import streamlit as st
import time
import httpx

st.set_page_config(page_title="Chat - LLMOps", page_icon="💬", layout="wide")

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("💬 Multi-Agent Chat")
st.markdown("Ask anything — the system routes to the best agent automatically.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"streamlit_{int(time.time())}"

with st.sidebar:
    st.markdown("### Session")
    st.text_input("Session ID", value=st.session_state.session_id, key="sid_input", disabled=True)

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.session_id = f"streamlit_{int(time.time())}"
        st.rerun()

    st.markdown("### Agent Routes")
    st.markdown("""
    | Route | Trigger |
    |-------|---------|
    | 💬 **CHAT** | hello, thanks, greetings |
    | 🔍 **WEB** | latest, news, weather |
    | 📖 **RAG** | questions about uploaded docs |
    """)

    st.markdown("### Tips")
    st.markdown("- Upload docs first for RAG answers")
    st.markdown("- Try: 'Latest AI news'")
    st.markdown("- Try: 'What did I upload?'")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "agent" in msg:
            st.caption(f"Agent: {msg['agent']} | Latency: {msg.get('latency', 'N/A')}ms")

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = httpx.post(
                    f"{API_URL}/chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "message": prompt,
                        "stream": False
                    },
                    timeout=120
                )
                data = response.json()

                if data.get("success"):
                    answer = data["data"]["answer"]
                    agent = data["data"]["agent"]
                    latency = data["data"].get("latency_ms", "N/A")

                    st.markdown(answer)
                    st.caption(f"Agent: {agent} | Latency: {latency}ms")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "agent": agent,
                        "latency": latency
                    })
                else:
                    errors = data.get("errors", ["Unknown error"])
                    st.error(f"Error: {', '.join(errors)}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Error: {', '.join(errors)}"
                    })
            except httpx.ConnectError:
                st.error("Cannot connect to API server. Is it running?")
            except Exception as e:
                st.error(f"Error: {str(e)}")
