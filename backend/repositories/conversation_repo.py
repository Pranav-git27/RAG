"""
Conversation + message repository — CRUD for chat sessions.

Each conversation groups a sequence of user / assistant messages.
Sources (retrieved document references) are stored as JSONB on assistant messages.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.models.db import Conversation, Message

logger = logging.getLogger("owasp-api")


class ConversationRepository:
    """Read / write operations on ``conversations`` and ``messages``."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------- Conversations
    def create_conversation(self, title: str | None = None) -> Conversation:
        """Start a new conversation and persist it."""
        conv = Conversation(id=uuid.uuid4(), title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get_conversation(self, conversation_id: uuid.UUID) -> Conversation | None:
        """Fetch a conversation by ID, or ``None`` if not found."""
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def list_conversations(
        self, limit: int = 20, offset: int = 0,
    ) -> list[Conversation]:
        """Return recent conversations ordered by updated_at desc."""
        return (
            self.db.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    # ----------------------------------------------------------- Messages
    def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        sources: list[dict[str, Any]] | None = None,
    ) -> Message:
        """Append a message to a conversation."""
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )
        self.db.add(msg)
        # Touch updated_at on the parent conversation.
        conv = self.get_conversation(conversation_id)
        if conv is not None:
            # The DB trigger handles this, but we nudge it here too for
            # consistency within the same transaction.
            from sqlalchemy import func
            self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
            ).update({Conversation.updated_at: func.now()})
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(
        self, conversation_id: uuid.UUID,
    ) -> list[Message]:
        """Return all messages in a conversation, oldest first."""
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
