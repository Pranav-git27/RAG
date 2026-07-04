"""
Centralised application configuration.

Single source of truth for all environment-driven settings, loaded once at
import time. Replaces the scattered ``os.environ.get`` calls that previously
lived across ``main.py``, ``ingest.py`` and ``database.py``.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env once, here, so every consumer sees the values.
load_dotenv()

logger = logging.getLogger("owasp-api")


class Settings(BaseSettings):
    """Strongly-typed settings read from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- Secrets / database --
    gemini_api_key: str
    database_url: str

    # -- Embeddings --
    embedding_model: str = "gemini-embedding-2"
    # MRL-truncated dimensionality. gemini-embedding-2 defaults to 3072; 768
    # keeps the pgvector column + HNSW index lean with negligible quality loss.
    embedding_dim: int = 768

    # -- Generation --
    llm_model: str = "gemini-2.5-flash"

    # -- Frontend convenience (Streamlit reads this) --
    backend_url: str = "http://127.0.0.1:8000"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the env file is parsed only once per process, regardless of how
    many modules import configuration.
    """
    settings = Settings()  # type: ignore[call-arg]
    logger.info(
        "Configuration loaded (embedding_model=%s, dim=%d, llm_model=%s)",
        settings.embedding_model,
        settings.embedding_dim,
        settings.llm_model,
    )
    return settings
