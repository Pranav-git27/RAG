"""
secOwasp — FastAPI application entry point.

Creates the app, registers routers, and configures lifespan (startup /
shutdown).  Start with:

    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.config import get_settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("owasp-api")

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: log config.  Shutdown: cleanup."""
    settings = get_settings()
    logger.info(
        "secOwasp starting — model=%s, dim=%d, llm=%s",
        settings.embedding_model,
        settings.embedding_dim,
        settings.llm_model,
    )
    yield
    logger.info("secOwasp shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="secOwasp — OWASP Semantic Search API",
    version="2.0.0",
    description=(
        "Production-grade RAG API integrating Supabase (Postgres + pgvector) "
        "with Google Gemini embeddings and generation."
    ),
    lifespan=lifespan,
)

# -- Register routers --
from backend.routes import health, search, conversations  # noqa: E402

app.include_router(health.router)
app.include_router(search.router)
app.include_router(conversations.router)
