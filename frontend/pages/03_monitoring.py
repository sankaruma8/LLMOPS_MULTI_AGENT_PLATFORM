import os
import streamlit as st
import json

st.set_page_config(page_title="Monitoring - LLMOps", page_icon="📊", layout="wide")

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("📊 Monitoring & System Status")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Metrics", "🖥️ System", "🔍 Audit Log", "⚡ Rate Limits"])

with tab1:
    st.markdown("### Performance Metrics")
    try:
        import httpx
        response = httpx.get(f"{API_URL}/metrics", timeout=10)
        data = response.json()

        if data.get("success"):
            metrics = data["data"]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Queries", metrics.get("total_queries", 0))
            col2.metric("Avg Latency", f"{metrics.get('avg_latency_ms', 0):.0f}ms")
            col3.metric("Success Rate", f"{metrics.get('success_rate', 0) * 100:.1f}%")
            col4.metric("Uptime", f"{metrics.get('uptime', 0):.0f}s")

            if "route_distribution" in metrics:
                st.markdown("#### Route Distribution")
                st.bar_chart(metrics["route_distribution"])
        else:
            st.info("No metrics available yet.")
    except httpx.ConnectError:
        st.error("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

    if st.button("🔄 Reset Metrics"):
        try:
            import httpx
            httpx.post(f"{API_URL}/metrics/reset", timeout=10)
            st.success("Metrics reset")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

with tab2:
    st.markdown("### System Status")
    try:
        import httpx
        response = httpx.get(f"{API_URL}/system/status", timeout=10)
        data = response.json()

        if data.get("success"):
            status = data["data"]
            st.json(status)

            features = status.get("features", {})
            st.markdown("#### Feature Flags")
            for feat, enabled in features.items():
                icon = "✅" if enabled else "❌"
                st.markdown(f"{icon} **{feat}**")
    except httpx.ConnectError:
        st.error("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

with tab3:
    st.markdown("### Audit Log")
    limit = st.slider("Limit", 10, 500, 50)

    try:
        import httpx
        response = httpx.get(f"{API_URL}/system/audit?limit={limit}", timeout=10)
        data = response.json()

        if data.get("success"):
            entries = data["data"]
            if entries:
                for entry in entries[-20:]:
                    with st.expander(f"📋 {entry.get('action', 'N/A')} - {entry.get('timestamp', 'N/A')}"):
                        st.json(entry)
            else:
                st.info("No audit entries yet.")
    except httpx.ConnectError:
        st.error("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

with tab4:
    st.markdown("### Rate Limit Status")
    try:
        import httpx
        response = httpx.get(f"{API_URL}/rate-limit/stats", timeout=10)
        data = response.json()

        if data.get("success"):
            stats = data["data"]
            st.json(stats)
    except httpx.ConnectError:
        st.error("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

    st.markdown("### Cache Status")
    try:
        import httpx
        response = httpx.get(f"{API_URL}/cache/stats", timeout=10)
        data = response.json()

        if data.get("success"):
            cache = data["data"]
            col1, col2 = st.columns(2)
            col1.metric("Embedding Cache", cache.get("embedding_cache_size", 0))
            web_cache = cache.get("web_search_cache", [])
            col2.metric("Web Search Cache", len(web_cache))
    except httpx.ConnectError:
        st.error("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

    if st.button("🗑️ Clear All Caches"):
        try:
            import httpx
            httpx.post(f"{API_URL}/cache/clear", timeout=10)
            st.success("Caches cleared")
        except Exception as e:
            st.error(f"Error: {str(e)}")
