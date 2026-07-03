"""
Retrieval service — orchestrates embedding + pgvector search.

Thin orchestration layer: embed the query, then delegate to the
DocumentRepository for the actual vector search.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.repositories.document_repo import DocumentRepository
from backend.services.embeddings import EmbeddingService

logger = logging.getLogger("owasp-api")


class RetrievalService:
    """Embed a query and retrieve the most similar documents."""

    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.document_repo = DocumentRepository(db)

    def retrieve(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """
        Embed *query*, then search pgvector for the top-*k* results.

        Returns the same shape as ``DocumentRepository.search_similar``:
        a list of dicts with id, content, score, and metadata fields.
        """
        query_vector = self.embedding_service.embed_query(query)
        results = self.document_repo.search_similar(query_vector, k=k)
        logger.info("retrieve(%d results) for query: %s", len(results), query[:60])
        return results
