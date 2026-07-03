"""
secOwasp — Streamlit frontend for OWASP semantic RAG search.

Thin entry point: applies the theme, renders the sidebar + chat loop,
and delegates rendering to ``components.py`` and API calls to ``api_client.py``.

Run with:
    streamlit run frontend/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so sibling-package imports work
# when Streamlit launches this file directly.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

from frontend.api_client import BackendClient
from frontend.components import render_answer, render_empty_state, render_status_indicator
from frontend.styles import inject_theme

# ---------------------------------------------------------------------------
# Page config (must be the FIRST Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="secOwasp — OWASP Semantic Search",
    page_icon="🛡️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Theme injection
# ---------------------------------------------------------------------------
inject_theme()

# ---------------------------------------------------------------------------
# Backend client (configurable via env or sidebar)
# ---------------------------------------------------------------------------
backend = BackendClient()

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("# 🛡️ secOwasp")
    st.caption("Secure Semantic Intelligence")
    st.divider()

    st.markdown("**System Status**")
    healthy = backend.is_healthy()
    render_status_indicator(healthy)
    st.session_state["backend_healthy"] = healthy

    st.divider()
    st.markdown("**Controls**")
    if st.button("🧹 Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.markdown("# secOwasp")
st.caption("Context-aware security intelligence for the OWASP Top 10.")
st.divider()

# ---------------------------------------------------------------------------
# Empty state (show only when no messages)
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    render_empty_state()

# ---------------------------------------------------------------------------
# Render conversation history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and "sources" in msg:
            render_answer(msg["content"], msg["sources"])
        else:
            st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Chat input + RAG search
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask a question about OWASP vulnerabilities…"):
    # Guard: backend must be reachable
    if not st.session_state.get("backend_healthy", False):
        st.error(
            "The backend service is not reachable. "
            "Please ensure the FastAPI server is running (uvicorn backend.main:app --port 8000)."
        )
        st.stop()

    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Query backend
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching knowledge base…"):
            try:
                result = backend.search(prompt, n_results=3)
            except Exception as e:
                st.error(f"Search failed: {e}")
                st.stop()

            answer = result.get("answer", "")
            sources = result.get("sources", [])

            render_answer(answer, sources)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
            })
