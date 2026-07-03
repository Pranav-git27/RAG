"""
Embedding service — the ONLY place Gemini embedding logic lives.

Replaces the two duplicate ``GeminiEmbeddingWrapper`` classes that previously
existed in ``main.py`` and ``ingest.py``.

Uses MRL-truncated 768-dimensional vectors to keep the pgvector column lean.
"""

from __future__ import annotations

import logging

from google import genai

from backend.config import get_settings

logger = logging.getLogger("owasp-api")

_settings = get_settings()


class EmbeddingService:
    """Wrapper around the Google GenAI SDK for embedding generation."""

    def __init__(self, client: genai.Client | None = None) -> None:
        self.client = client or genai.Client(api_key=_settings.gemini_api_key)
        self.model = _settings.embedding_model
        self.dim = _settings.embedding_dim

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string and return the vector."""
        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config={"output_dimensionality": self.dim},
            )
            # Extract vector from the response.
            if hasattr(response, "embeddings") and response.embeddings:
                return response.embeddings[0].values
            elif hasattr(response, "embedding") and response.embedding:
                return response.embedding.values
            elif isinstance(response, list):
                return response[0].values
            else:
                return response.values  # type: ignore[return-value]
        except Exception:
            logger.exception("Embedding generation failed for query.")
            raise

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents and return a list of vectors."""
        embeddings: list[list[float]] = []
        for text in texts:
            embeddings.append(self.embed_query(text))
        return embeddings
