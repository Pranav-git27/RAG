"""
FastAPI dependency providers.

Thin wiring layer that gives route handlers access to the DB session,
embedding service, and other shared resources.  Keeps route functions
clean and testable (dependencies can be overridden with mocks).
"""

from __future__ import annotations

import logging

from fastapi import Depends
from google import genai
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.db.session import SessionLocal
from backend.repositories.conversation_repo import ConversationRepository
from backend.repositories.document_repo import DocumentRepository
from backend.services.embeddings import EmbeddingService
from backend.services.generation import GenerationService
from backend.services.retrieval import RetrievalService

logger = logging.getLogger("owasp-api")
_settings = get_settings()


# ---------------------------------------------------------------------------
# Shared service singletons (created once at module load)
# ---------------------------------------------------------------------------
_gemini_client = genai.Client(api_key=_settings.gemini_api_key)
_embedding_service = EmbeddingService(client=_gemini_client)
_generation_service = GenerationService(client=_gemini_client)


# ---------------------------------------------------------------------------
# FastAPI dependency functions
# ---------------------------------------------------------------------------
def get_db() -> Session:
    """Yield a database session (closed after the request)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_embedding_service() -> EmbeddingService:
    """Return the shared EmbeddingService."""
    return _embedding_service


def get_generation_service() -> GenerationService:
    """Return the shared GenerationService."""
    return _generation_service


def get_document_repo(db: Session = Depends(get_db)) -> DocumentRepository:
    """Return a DocumentRepository bound to the current request's DB session."""
    return DocumentRepository(db)


def get_conversation_repo(db: Session = Depends(get_db)) -> ConversationRepository:
    """Return a ConversationRepository bound to the current request's DB session."""
    return ConversationRepository(db)


def get_retrieval_service(
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RetrievalService:
    """Return a RetrievalService bound to the current request's DB session."""
    return RetrievalService(db, embedding_service)
