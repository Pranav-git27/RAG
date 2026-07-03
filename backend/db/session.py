"""
SQLAlchemy 2.0 engine, session factory and declarative base.

Engine settings are tuned for Supabase's connection-pooler Postgres
(Session mode, port 6543).
"""

from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import get_settings

logger = logging.getLogger("owasp-api")

_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,   # verify connections are alive before checkout
    pool_recycle=1800,    # recycle before Supabase idle timeout closes them
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models in ``backend.models.db``."""


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a DB session and ensure it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
