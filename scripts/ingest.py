"""
secOwasp — Ingest / seeding script.

Embeds sample OWASP records using Gemini and inserts them into the Supabase
pgvector-backed ``documents`` table.  Run once (or to re-seed after a reset).

    python scripts/ingest.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure the project root is on sys.path so ``backend.*`` imports work
# regardless of where the script is invoked from.
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(Path(PROJECT_ROOT) / ".env")

from backend.config import get_settings
from backend.db.session import SessionLocal
from backend.repositories.document_repo import DocumentRepository
from backend.services.embeddings import EmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("ingest")


# ---------------------------------------------------------------------------
# Sample OWASP records (same data as the original ingest.py, restructured)
# ---------------------------------------------------------------------------
SEED_RECORDS = [
    {
        "content": (
            "## A01:2025 – Broken Access Control\n\n"
            "Access control enforces policy such that users cannot act outside "
            "of their intended permissions. Failures typically lead to "
            "unauthorized information disclosure, modification, or destruction "
            "of data. Common vectors include insecure direct object references "
            "(IDOR), missing function-level access control, and CORS "
            "misconfigurations."
        ),
        "owasp_category": "A01:2025-Broken Access Control",
        "chunk_type": "description",
        "target_language": "markdown",
    },
    {
        "content": (
            "## Remediation: Enforce Server-Side Access Checks\n\n"
            "Never rely solely on client-side controls. Every API endpoint and "
            "server-side route must verify the authenticated user's identity "
            "and role before performing any action. Use deny-by-default "
            "policies and log all access control failures."
        ),
        "owasp_category": "A01:2025-Broken Access Control",
        "chunk_type": "remediation",
        "target_language": "markdown",
    },
    {
        "content": (
            "from functools import wraps\n"
            "from fastapi import Depends, HTTPException\n\n"
            "def require_role(required_role: str):\n"
            '    """Secure Python decorator to enforce role-based access control."""\n'
            "    def decorator(func):\n"
            "        @wraps(func)\n"
            "        def wrapper(*args, current_user=Depends(get_current_user), **kwargs):\n"
            '            if current_user.role != required_role:\n'
            '                raise HTTPException(status_code=403, detail="Insufficient permissions")\n'
            "            return func(*args, current_user=current_user, **kwargs)\n"
            "        return wrapper\n"
            "    return decorator"
        ),
        "owasp_category": "A01:2025-Broken Access Control",
        "chunk_type": "code_example",
        "target_language": "python",
    },
]


def seed() -> None:
    """Embed and insert the seed records into Supabase."""
    settings = get_settings()
    logger.info("Embedding model: %s (dim=%d)", settings.embedding_model, settings.embedding_dim)

    # Initialise services
    embedding_service = EmbeddingService()
    db = SessionLocal()
    repo = DocumentRepository(db)

    # Check current count
    existing = repo.count()
    if existing > 0:
        logger.info(
            "Database already has %d documents. Skipping seed "
            "(delete from documents if you want to re-seed).",
            existing,
        )
        db.close()
        return

    # Embed all documents
    logger.info("Embedding %d documents…", len(SEED_RECORDS))
    texts = [r["content"] for r in SEED_RECORDS]
    embeddings = embedding_service.embed_documents(texts)

    # Build records with embeddings
    records = []
    for rec, emb in zip(SEED_RECORDS, embeddings):
        records.append({**rec, "embedding": emb})

    # Bulk insert
    inserted = repo.add_documents_bulk(records)
    logger.info("Seeded %d documents into 'documents' table.", inserted)
    db.close()


if __name__ == "__main__":
    seed()
