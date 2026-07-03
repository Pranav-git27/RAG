"""
Theme constants and CSS for the Streamlit frontend.

Single source of truth for all visual styling. Injected once via
``st.markdown(css, unsafe_allow_html=True)`` — no more 150-line inline blobs.
"""

THEME = {
    "bg_primary": "#0D1117",
    "bg_secondary": "#1A2333",
    "accent": "#00E676",
    "accent_dark": "#00C853",
    "text_primary": "#E2E8F0",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "border": "rgba(255, 255, 255, 0.05)",
    "card_bg": "rgba(255, 255, 255, 0.02)",
    "success": "#00E676",
    "error": "#EF4444",
}

# NOTE: This font URL is fetched at runtime from Google Fonts.
FONT_IMPORT = "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap"

CSS = f"""
<style>
    @import url('{FONT_IMPORT}');

    /* ── Base ──────────────────────────────────────────────────────────── */
    .stApp {{
        background: radial-gradient(circle at 50% 50%, #1A2333 0%, #0D1117 100%);
        color: {THEME["text_primary"]};
        font-family: 'Outfit', sans-serif;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background:
            radial-gradient(at 0% 0%, rgba(0, 230, 118, 0.05) 0, transparent 50%),
            radial-gradient(at 100% 100%, rgba(0, 122, 255, 0.05) 0, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }}

    /* ── Sidebar ────────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {{
        background-color: rgba(26, 35, 51, 0.8) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid {THEME["border"]};
    }}

    section[data-testid="stSidebar"] .stButton > button {{
        background: linear-gradient(135deg, rgba(0, 230, 118, 0.1) 0%, rgba(0, 230, 118, 0.05) 100%);
        color: {THEME["accent"]};
        border: 1px solid rgba(0, 230, 118, 0.3);
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: linear-gradient(135deg, {THEME["accent"]} 0%, {THEME["accent_dark"]} 100%);
        color: #121824;
        border-color: {THEME["accent"]};
        box-shadow: 0 4px 15px rgba(0, 230, 118, 0.3);
        transform: translateY(-1px);
    }}

    /* ── Chat Input ────────────────────────────────────────────────────── */
    div[data-testid="stChatInput"] {{
        background-color: transparent !important;
        padding-bottom: 2rem;
    }}

    div[data-testid="stChatInput"] textarea {{
        background-color: rgba(26, 35, 51, 0.9) !important;
        backdrop-filter: blur(8px);
        color: {THEME["text_primary"]};
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }}

    div[data-testid="stChatInput"] textarea:focus {{
        border-color: {THEME["accent"]} !important;
        box-shadow: 0 0 0 1px {THEME["accent"]}, 0 4px 20px rgba(0, 230, 118, 0.1);
    }}

    /* ── Chat Messages ───────────────────────────────────────────────── */
    div[data-testid="stChatMessage"] {{
        animation: slideInUp 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
        background-color: {THEME["card_bg"]} !important;
        border: 1px solid {THEME["border"]};
        border-radius: 16px;
        margin-bottom: 1rem;
        padding: 1rem !important;
    }}

    @keyframes slideInUp {{
        from {{ opacity: 0; transform: translateY(20px) scale(0.98); }}
        to   {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}

    /* ── Typography ─────────────────────────────────────────────────────── */
    h1, h2, h3 {{
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }}

    /* ── Scrollbar ──────────────────────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(0, 230, 118, 0.3);
    }}
</style>
"""


def inject_theme() -> None:
    """Call once at the top of app.py to apply the theme."""
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)
