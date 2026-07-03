"""
Document repository — pgvector similarity search and bulk insertion.

All vector operations go through SQLAlchemy Core (textual SQL) because the
``pgvector`` ``<=>`` cosine-distance operator is not expressible in pure
ORM.  The HNSW index defined in ``init_db.sql`` accelerates these queries.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, Select, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session

from backend.models.db import Document

logger = logging.getLogger("owasp-api")


class DocumentRepository:
    """Read / write operations on the ``documents`` table."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ CRUD
    def add_document(
        self,
        content: str,
        embedding: list[float],
        owasp_category: str | None = None,
        chunk_type: str | None = None,
        target_language: str | None = None,
        cwe_id: str | None = None,
        severity: str | None = None,
        source: str | None = None,
    ) -> Document:
        """Insert a single document row and return the ORM instance."""
        doc = Document(
            id=uuid.uuid4(),
            content=content,
            embedding=embedding,
            owasp_category=owasp_category,
            chunk_type=chunk_type,
            target_language=target_language,
            cwe_id=cwe_id,
            severity=severity,
            source=source,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def add_documents_bulk(self, records: list[dict[str, Any]]) -> int:
        """Insert many documents in a single commit. Returns count inserted."""
        docs = [
            Document(
                id=r.get("id", uuid.uuid4()),
                content=r["content"],
                embedding=r["embedding"],
                owasp_category=r.get("owasp_category"),
                chunk_type=r.get("chunk_type"),
                target_language=r.get("target_language"),
                cwe_id=r.get("cwe_id"),
                severity=r.get("severity"),
                source=r.get("source"),
            )
            for r in records
        ]
        self.db.add_all(docs)
        self.db.commit()
        return len(docs)

    def count(self) -> int:
        """Return total number of documents (used by health probe)."""
        return self.db.query(Document).count()

    # --------------------------------------------------------- Vector search
    def search_similar(
        self,
        query_embedding: list[float],
        k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Retrieve the top-*k* most similar documents using cosine distance.

        Returns a list of dicts with keys: id, content, score, owasp_category,
        chunk_type, target_language.  ``score`` is 1 - cosine_distance
        (i.e. cosine similarity, 0–1).
        """
        # Raw SQL keeps the <=> operator explicit and readable.
        stmt = text(
            """
            SELECT
                id,
                content,
                1 - (embedding <=> CAST(:qvec AS vector)) AS score,
                owasp_category,
                chunk_type,
                target_language,
                severity,
                cwe_id,
                source
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :k
            """
        )
        rows = self.db.execute(
            stmt,
            {"qvec": query_embedding, "k": k},
        ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append({
                "id": str(row.id),
                "content": row.content,
                "score": float(row.score),
                "owasp_category": row.owasp_category,
                "chunk_type": row.chunk_type,
                "target_language": row.target_language,
                "severity": row.severity,
                "cwe_id": row.cwe_id,
                "source": row.source,
            })
        logger.info("search_similar returned %d results (k=%d)", len(results), k)
        return results
