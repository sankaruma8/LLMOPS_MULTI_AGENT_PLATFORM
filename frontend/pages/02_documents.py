import os
import streamlit as st
import time

st.set_page_config(page_title="Documents - LLMOps", page_icon="📄", layout="wide")

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("📄 Document Management")
st.markdown("Upload PDFs for RAG-powered question answering.")

tab1, tab2 = st.tabs(["📤 Upload", "📋 Documents"])

with tab1:
    st.markdown("### Upload PDF")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF to add it to the knowledge base"
    )

    session_id = st.text_input("Session ID", value=f"upload_{int(time.time())}")

    if uploaded_file and st.button("📤 Upload", type="primary"):
        with st.spinner("Uploading and processing..."):
            try:
                import httpx
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = httpx.post(
                    f"{API_URL}/upload",
                    files=files,
                    timeout=600
                )
                data = response.json()

                if data.get("success"):
                    result = data.get("data", {})
                    st.success(f"Uploaded: {uploaded_file.name}")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Chunks", result.get("chunk_count", 0))
                    col2.metric("Pages", result.get("page_count", 0))
                    col3.metric("Version", result.get("version", 1))

                    if result.get("is_duplicate"):
                        st.info("Note: This file was already uploaded (duplicate detected)")
                else:
                    st.error(f"Upload failed: {data.get('error', 'Unknown error')}")
            except httpx.ConnectError:
                st.error("Cannot connect to API server.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("---")
    st.markdown("### Batch Upload")
    batch_files = st.file_uploader(
        "Choose multiple PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="batch"
    )

    if batch_files and st.button("📤 Upload All"):
        with st.spinner(f"Uploading {len(batch_files)} files..."):
            try:
                import httpx
                results = []
                for f in batch_files:
                    files = {"file": (f.name, f.getvalue(), "application/pdf")}
                    resp = httpx.post(f"{API_URL}/upload", files=files, timeout=120)
                    results.append(resp.json())

                success = sum(1 for r in results if r.get("success"))
                st.success(f"Uploaded {success}/{len(batch_files)} files")
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tab2:
    st.markdown("### Uploaded Documents")

    try:
        import httpx
        response = httpx.get(f"{API_URL}/upload/list", timeout=10)
        data = response.json()

        if data.get("success"):
            docs = data.get("data", [])
            if docs:
                for doc in docs:
                    with st.expander(f"📄 {doc.get('filename', 'Unknown')}"):
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Chunks", doc.get("chunk_count", 0))
                        col2.metric("Pages", doc.get("page_count", 0))
                        col3.metric("Version", doc.get("version", 1))
                        col4.metric("Size", f"{doc.get('file_size', 0) / 1024:.1f} KB")
                        st.caption(f"Uploaded: {doc.get('upload_date', 'N/A')}")
            else:
                st.info("No documents uploaded yet.")
        else:
            st.info("No documents found.")
    except httpx.ConnectError:
        st.error("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
