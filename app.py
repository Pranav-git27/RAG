"""
secOwasp — Animated, reactive Streamlit frontend for OWASP semantic search.

Connects to the FastAPI backend at ``http://127.0.0.1:8000``.
Theme: Cyber-Defensive Dusk (dark slate / emerald accents).
"""

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE = "http://127.0.0.1:8000"
SEARCH_ENDPOINT = f"{API_BASE}/api/v1/search"
HEALTH_ENDPOINT = f"{API_BASE}/health"
PAGE_TITLE = "secOwasp — OWASP Semantic Search"
PAGE_ICON = "🛡️"

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

# ---------------------------------------------------------------------------
# Injected CSS — Premium Cyber-Defensive Dusk Theme
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    /* ── Base ──────────────────────────────────────────────────────────── */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #1A2333 0%, #0D1117 100%);
        color: #E2E8F0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Animated mesh background overlay */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: 
            radial-gradient(at 0% 0%, rgba(0, 230, 118, 0.05) 0, transparent 50%),
            radial-gradient(at 100% 100%, rgba(0, 122, 255, 0.05) 0, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }

    /* ── Sidebar Glassmorphism ──────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: rgba(26, 35, 51, 0.8) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, rgba(0, 230, 118, 0.1) 0%, rgba(0, 230, 118, 0.05) 100%);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.3);
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #00E676 0%, #00C853 100%);
        color: #121824;
        border-color: #00E676;
        box-shadow: 0 4px 15px rgba(0, 230, 118, 0.3);
        transform: translateY(-1px);
    }

    /* ── Chat Input ────────────────────────────────────────────────────── */
    div[data-testid="stChatInput"] {
        background-color: transparent !important;
        padding-bottom: 2rem;
    }
    
    div[data-testid="stChatInput"] textarea {
        background-color: rgba(26, 35, 51, 0.9) !important;
        backdrop-filter: blur(8px);
        color: #E2E8F0;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    div[data-testid="stChatInput"] textarea:focus {
        border-color: #00E676 !important;
        box-shadow: 0 0 0 1px #00E676, 0 4px 20px rgba(0, 230, 118, 0.1);
    }

    /* ── Chat Messages ─────────────────────────────────────────────────── */
    div[data-testid="stChatMessage"] {
        animation: slideInUp 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        margin-bottom: 1rem;
        padding: 1rem !important;
    }
    
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background-color: rgba(0, 230, 118, 0.05) !important;
        border-color: rgba(0, 230, 118, 0.1);
    }

    @keyframes slideInUp {
        from { opacity: 0; transform: translateY(20px) scale(0.98); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* ── Typography & Accents ───────────────────────────────────────────── */
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #00E676 0%, #00C853 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ── Status Pulse ───────────────────────────────────────────────────── */
    .status-pulse {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online {
        background-color: #00E676;
        box-shadow: 0 0 8px #00E676;
        animation: pulse-green 2s infinite;
    }
    
    .status-offline {
        background-color: #EF4444;
        box-shadow: 0 0 8px #EF4444;
        animation: pulse-red 2s infinite;
    }

    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(0, 230, 118, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
    }
    
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    /* ── Modern Scrollbar ───────────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 230, 118, 0.3);
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "backend_available" not in st.session_state:
    st.session_state.backend_available = False

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"<h2 class='gradient-text' style='margin-bottom:0;'>{PAGE_ICON} secOwasp</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#94A3B8; font-size:0.85rem; margin-top:0; font-weight:300;'>"
        "Secure Semantic Intelligence</p>",
        unsafe_allow_html=True,
    )
    st.divider()
    
    st.markdown(
        "<p style='color:#E2E8F0; font-size:0.95rem; margin-bottom:0.5rem;'><strong>System Status</strong></p>",
        unsafe_allow_html=True,
    )

    # Backend health indicator
    try:
        r = requests.get(HEALTH_ENDPOINT, timeout=3)
        if r.status_code == 200 and r.json().get("status") == "healthy":
            st.session_state.backend_available = True
            st.markdown(
                f"<div style='display:flex; align-items:center;'>"
                f"<span class='status-pulse status-online'></span>"
                f"<span style='color:#00E676; font-size:0.85rem;'>Backend Operational</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.session_state.backend_available = False
            st.markdown(
                f"<div style='display:flex; align-items:center;'>"
                f"<span class='status-pulse status-offline'></span>"
                f"<span style='color:#EF4444; font-size:0.85rem;'>Backend Offline</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    except requests.RequestException:
        st.session_state.backend_available = False
        st.markdown(
            f"<div style='display:flex; align-items:center;'>"
            f"<span class='status-pulse status-offline'></span>"
            f"<span style='color:#EF4444; font-size:0.85rem;'>Connection Failed</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown(
        "<p style='color:#E2E8F0; font-size:0.9rem;'><strong>Controls</strong></p>",
        unsafe_allow_html=True,
    )
    if st.button("🧹 Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# Title area
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 class='gradient-text' style='font-size:2.5rem; margin-bottom:0;'>secOwasp</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#94A3B8; font-size:1.1rem; margin-top:0; font-weight:300;'>"
    "Context-aware security intelligence for the OWASP Top 10.</p>",
    unsafe_allow_html=True,
)
st.divider()

# ---------------------------------------------------------------------------
# Render conversation history
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown(
        """
        <div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); border-radius:24px; padding:3rem; text-align:center; margin:2rem 0;'>
            <h2 class='gradient-text'>Security Intelligence Ready</h2>
            <p style='color:#94A3B8; font-size:1.1rem; max-width:600px; margin:1rem auto;'>
                Ask me about OWASP Top 10 vulnerabilities, detection methods, or remediation strategies. 
                I'll search the knowledge base and provide context-aware insights.
            </p>
            <div style='display:flex; justify-content:center; gap:1rem; margin-top:2rem;'>
                <span style='background:rgba(0,230,118,0.1); color:#00E676; padding:0.5rem 1rem; border-radius:20px; font-size:0.85rem;'>🛡️ Broken Access Control</span>
                <span style='background:rgba(0,230,118,0.1); color:#00E676; padding:0.5rem 1rem; border-radius:20px; font-size:0.85rem;'>🧪 Injection Attacks</span>
                <span style='background:rgba(0,230,118,0.1); color:#00E676; padding:0.5rem 1rem; border-radius:20px; font-size:0.85rem;'>📦 Supply Chain Risks</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask a question about OWASP vulnerabilities…"):
    # Guard: ensure backend is alive before accepting input
    if not st.session_state.backend_available:
        st.error(
            "The backend service is not reachable. "
            "Please ensure the FastAPI server is running on port 8000."
        )
        st.stop()

    # Append user message immediately (no flicker)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Query the backend with a spinner
    with st.chat_message("assistant"):
        with st.spinner("🔍 Scanning knowledge base…"):
            try:
                resp = requests.post(
                    SEARCH_ENDPOINT,
                    json={"text": prompt, "n_results": 3},
                    timeout=30,
                )
                resp.raise_for_status()
                results = resp.json()
            except requests.Timeout:
                st.error("The request timed out. Please try again.")
                st.stop()
            except requests.RequestException as e:
                detail = "Backend is offline or returned an error."
                if hasattr(e, "response") and e.response is not None:
                    try:
                        detail = e.response.json().get(
                            "detail", e.response.text
                        )
                    except Exception:
                        detail = e.response.text
                st.error(f"Search failed: {detail}")
                st.stop()

        # Build a readable markdown response from the result list
        if not results:
            st.markdown(
                "*No matching results found in the OWASP knowledge base.*"
            )
        else:
            response_parts = [
                f"<h3 style='color:#E2E8F0; margin-bottom:1.5rem;'>🔎 Intelligence Summary ({len(results)} Matches)</h3>"
            ]
            for idx, item in enumerate(results, start=1):
                doc = item.get("document", "No content")
                meta = item.get("metadata", {}) or {}
                dist = item.get("distance", 0.0)
                
                cat = meta.get('owasp_category', 'Security Entry')
                type_label = meta.get('chunk_type', '').replace('_', ' ').upper()
                lang = meta.get('target_language', '').upper()
                
                # Pre-process doc to avoid backslashes in f-strings (for Python < 3.12 compatibility)
                safe_doc = doc.replace('\n', '<br>')

                # Dedented HTML to prevent Streamlit from treating it as a code block
                card_html = (
                    f"<div style='background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:16px; padding:1.5rem; margin-bottom:1.5rem;'>"
                    f"<div style='display:flex; justify-content:space-between; align-items:start; margin-bottom:1rem;'>"
                    f"<div style='flex-grow:1;'>"
                    f"<span style='color:#00E676; font-size:0.75rem; font-weight:700; letter-spacing:1px;'>{type_label}</span>"
                    f"<h4 style='margin:0.2rem 0; color:#F8FAFC;'>{cat}</h4>"
                    f"</div>"
                    f"<div style='text-align:right;'>"
                    f"<span style='background:rgba(0,230,118,0.1); color:#00E676; padding:0.2rem 0.6rem; border-radius:8px; font-size:0.7rem; font-weight:600;'>{lang}</span>"
                    f"</div>"
                    f"</div>"
                    f"<div style='color:#CBD5E1; font-size:0.95rem; line-height:1.6;'>"
                    f"{safe_doc}"
                    f"</div>"
                    f"<div style='margin-top:1.2rem; padding-top:0.8rem; border-top:1px solid rgba(255,255,255,0.03); display:flex; justify-content:space-between; align-items:center;'>"
                    f"<span style='color:#64748B; font-size:0.75rem;'>Confidence Index: {max(0, 1-dist):.2%}</span>"
                    f"<span style='color:#475569; font-size:0.7rem;'>ID: {idx:02d}</span>"
                    f"</div>"
                    f"</div>"
                )
                response_parts.append(card_html)

            full_response = "\n\n".join(response_parts)
            st.markdown(full_response, unsafe_allow_html=True)

            # Persist assistant response to session state
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

