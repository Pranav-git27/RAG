"""
Pydantic v2 request / response schemas for the FastAPI routes.

Input guards are preserved from the original ``main.py``:
  - ``text``: 3–500 characters (DoS / payload-size mitigation).
  - ``n_results``: 1–10 (resource-exhaustion prevention).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """Strictly-validated search request body."""

    text: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural-language search query (3-500 characters).",
    )
    n_results: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of top-K results to return (1-10).",
    )


class ConversationCreate(BaseModel):
    """Payload to start a new conversation."""

    title: str | None = Field(default=None, max_length=200)


class MessageCreate(BaseModel):
    """Payload to add a message to a conversation."""

    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1)
    sources: list[dict[str, Any]] | None = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class SourceItem(BaseModel):
    """A single retrieved document reference returned alongside the answer."""

    id: str
    content: str
    score: float
    owasp_category: str | None = None
    chunk_type: str | None = None
    target_language: str | None = None


class SearchResponse(BaseModel):
    """The full RAG response: synthesised answer + cited sources."""

    answer: str
    sources: list[SourceItem]
    query: str
    n_results: int


class HealthResponse(BaseModel):
    """Readiness-probe response."""

    status: str
    db: str


class ConversationResponse(BaseModel):
    """A conversation summary (no messages — fetched separately)."""

    id: str
    title: str | None
    created_at: str
    updated_at: str


class ConversationDetail(BaseModel):
    """A conversation with its full message history."""

    id: str
    title: str | None
    created_at: str
    updated_at: str
    messages: list[dict[str, Any]]
