"""
Reusable Streamlit UI components.

Each function renders one self-contained piece of the interface using
native Streamlit components (no ``unsafe_allow_html`` for user content —
XSS-safe by default).
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.styles import THEME


def render_empty_state() -> None:
    """Show the welcome / empty-state prompt."""
    st.markdown("")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<span style='background:rgba(0,230,118,0.1);color:{THEME['accent']};"
            f"padding:0.5rem 1rem;border-radius:20px;font-size:0.85rem;'>"
            f"🛡️ Broken Access Control</span>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"<span style='background:rgba(0,230,118,0.1);color:{THEME['accent']};"
            f"padding:0.5rem 1rem;border-radius:20px;font-size:0.85rem;'>"
            f"🧪 Injection Attacks</span>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"<span style='background:rgba(0,230,118,0.1);color:{THEME['accent']};"
            f"padding:0.5rem 1rem;border-radius:20px;font-size:0.85rem;'>"
            f"📦 Supply Chain Risks</span>",
            unsafe_allow_html=True,
        )


def render_answer(answer: str, sources: list[dict[str, Any]]) -> None:
    """
    Render the synthesised RAG answer followed by expandable source cards.

    The answer itself is rendered via ``st.markdown`` (safe — Streamlit
    escapes raw HTML).  Sources go into ``st.expander`` so they don't
    clutter the main view.
    """
    # Main answer
    st.markdown(answer)

    # Sources section
    if sources:
        st.divider()
        st.markdown(f"**Sources** ({len(sources)} retrieved)")
        for idx, src in enumerate(sources, start=1):
            score = src.get("score", 0)
            category = src.get("owasp_category", "Security Entry")
            chunk_type = src.get("chunk_type", "").replace("_", " ").upper()
            lang = src.get("target_language", "").upper()
            content = src.get("content", "No content")

            with st.expander(f"[{idx}] {category} — {chunk_type} ({lang}) — {score:.0%} match"):
                st.caption(content)


def render_status_indicator(healthy: bool) -> None:
    """Render a coloured status dot + label in the sidebar."""
    if healthy:
        st.markdown(
            f"<span style='color:{THEME['success']};font-size:0.85rem;'>"
            f"● Backend Operational</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<span style='color:{THEME['error']};font-size:0.85rem;'>"
            f"● Backend Offline</span>",
            unsafe_allow_html=True,
        )
