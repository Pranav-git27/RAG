"""
Search route — the core RAG endpoint.

Flow:  query → embed → pgvector search → LLM synthesis → persist → respond
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.deps import (
    get_db,
    get_document_repo,
    get_embedding_service,
    get_generation_service,
    get_retrieval_service,
    get_conversation_repo,
)
from backend.models.db import AuditLog
from backend.models.schemas import QueryRequest, SearchResponse, SourceItem

logger = logging.getLogger("owasp-api")

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    request: QueryRequest,
    db: Session = Depends(get_db),
    retrieval_service=Depends(get_retrieval_service),
    generation_service=Depends(get_generation_service),
) -> SearchResponse:
    """
    Execute a semantic RAG search against the OWASP knowledge base.

    1. Embed the query using Gemini.
    2. Retrieve top-K documents from pgvector.
    3. Synthesise an answer with gemini-2.0-flash.
    4. Return the answer + cited sources.
    """
    start = time.perf_counter()

    try:
        # Step 1–2: Retrieve
        documents = retrieval_service.retrieve(request.text, k=request.n_results)

        # Step 3: Generate
        answer = generation_service.synthesize(request.text, documents)

    except Exception:
        latency = int((time.perf_counter() - start) * 1000)
        _write_audit(db, "search", request.text, request.n_results, latency, "error")
        logger.exception("RAG pipeline failed.")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request.",
        )

    latency = int((time.perf_counter() - start) * 1000)
    _write_audit(db, "search", request.text, request.n_results, latency, "ok")

    # Step 4: Format response
    sources = [
        SourceItem(
            id=doc["id"],
            content=doc["content"],
            score=doc["score"],
            owasp_category=doc.get("owasp_category"),
            chunk_type=doc.get("chunk_type"),
            target_language=doc.get("target_language"),
        )
        for doc in documents
    ]

    return SearchResponse(
        answer=answer,
        sources=sources,
        query=request.text,
        n_results=len(sources),
    )


def _write_audit(
    db: Session,
    event_type: str,
    query: str,
    n_results: int,
    latency_ms: int,
    status: str,
) -> None:
    """Persist an audit log entry (fire-and-forget within the session)."""
    try:
        log = AuditLog(
            event_type=event_type,
            query=query,
            n_results=n_results,
            latency_ms=latency_ms,
            status=status,
        )
        db.add(log)
        db.commit()
    except Exception:
        logger.exception("Failed to write audit log (non-fatal).")
