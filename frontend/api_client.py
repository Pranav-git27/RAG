"""
Typed HTTP client for the secOwasp FastAPI backend.

Centralises all backend communication in one place so the Streamlit UI
never touches ``requests`` directly. The base URL is configurable via
env var or sidebar input.
"""

from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8000"


class BackendClient:
    """Typed wrapper around the secOwasp API."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("BACKEND_URL", "")).rstrip("/") or DEFAULT_BASE_URL
        self.timeout = 30

    # ------------------------------------------------------------------ Health
    def health(self) -> dict[str, str]:
        """Ping /health.  Returns the JSON body or raises on failure."""
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def is_healthy(self) -> bool:
        """Return True if the backend is reachable and healthy."""
        try:
            data = self.health()
            return data.get("status") == "healthy" and data.get("db") == "connected"
        except requests.RequestException:
            return False

    # ------------------------------------------------------------------ Search
    def search(self, text: str, n_results: int = 3) -> dict[str, Any]:
        """
        POST /api/v1/search — the RAG endpoint.

        Returns { answer, sources[], query, n_results }.
        """
        resp = requests.post(
            f"{self.base_url}/api/v1/search",
            json={"text": text, "n_results": n_results},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------- Conversations
    def list_conversations(self, limit: int = 20) -> list[dict[str, Any]]:
        """GET /api/v1/conversations"""
        resp = requests.get(
            f"{self.base_url}/api/v1/conversations",
            params={"limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def create_conversation(self, title: str | None = None) -> dict[str, Any]:
        """POST /api/v1/conversations"""
        resp = requests.post(
            f"{self.base_url}/api/v1/conversations",
            json={"title": title},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        """GET /api/v1/conversations/{id}"""
        resp = requests.get(
            f"{self.base_url}/api/v1/conversations/{conversation_id}",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
