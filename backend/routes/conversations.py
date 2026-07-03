"""
Conversation routes — list, create, and view chat sessions.

These are new endpoints that didn't exist in the original app. They enable
the Streamlit frontend to persist and reload conversation history.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.deps import get_db, get_conversation_repo
from backend.models.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationResponse,
)

logger = logging.getLogger("owasp-api")

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[ConversationResponse]:
    """Return recent conversations (newest first)."""
    repo = get_conversation_repo(db)
    convs = repo.list_conversations(limit=limit, offset=offset)
    return [
        ConversationResponse(
            id=str(c.id),
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in convs
    ]


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Start a new conversation."""
    repo = get_conversation_repo(db)
    conv = repo.create_conversation(title=payload.title)
    return ConversationResponse(
        id=str(conv.id),
        title=conv.title,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> ConversationDetail:
    """Fetch a conversation with its full message history."""
    repo = get_conversation_repo(db)
    try:
        conv_id = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format.")

    conv = repo.get_conversation(conv_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = repo.get_messages(conv_id)
    return ConversationDetail(
        id=str(conv.id),
        title=conv.title,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
        messages=[
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    )
