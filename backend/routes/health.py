"""
Health / readiness probe route.

Returns 200 only when the database connection is verified.  The lightweight
``SELECT 1`` checks that Supabase is reachable before accepting traffic.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.deps import get_db
from backend.models.schemas import HealthResponse

logger = logging.getLogger("owasp-api")

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Readiness probe — verifies Supabase Postgres is reachable."""
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(status="healthy", db="connected")
    except Exception:
        logger.exception("Health check — database unreachable.")
        raise HTTPException(
            status_code=503,
            detail="Database service is not available. Please try again shortly.",
        )
