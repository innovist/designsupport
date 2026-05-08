"""Conversation Django ORM models.

Implements chat-based collaboration.
INV-01-03: AI messages must provide evidence_refs OR be flagged as hypothesis.
"""
from django.db import models
from shared.infrastructure.orm.base_model import TimestampedModel


class Conversation(TimestampedModel):
    """Conversation model for session chat.

    Groups messages within a design session.
    """

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(unique=True, db_index=True)

    class Meta:
        db_table = "conversations"
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self) -> str:
        return f"Conversation for session {self.session_id}"


class ChatMessageManager(models.Manager):
    """Manager for chat message queries."""

    def for_conversation(self, conversation_id):
        """Filter messages by conversation."""
        return self.filter(conversation_id=conversation_id).order_by("created_at")

    def ai_messages(self):
        """Get only AI messages."""
        return self.filter(role__in=["assistant", "system"])

    def user_messages(self):
        """Get only user messages."""
        return self.filter(role="user")


class ChatMessage(TimestampedModel):
    """Chat message model.

    Individual messages within conversations.
    """

    id = models.UUIDField(primary_key=True)
    conversation_id = models.UUIDField(db_index=True)
    role = models.CharField(
        max_length=10,
        choices=[("user", "User"), ("assistant", "Assistant"), ("system", "System")],
    )
    content = models.TextField()
    evidence_refs = models.JSONField(default=list)
    is_hypothesis = models.BooleanField(default=False)

    objects = ChatMessageManager()

    class Meta:
        db_table = "chat_messages"
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
        indexes = [
            models.Index(fields=["conversation_id", "created_at"]),
        ]
        # INV-01-03 constraint is enforced at the DB level via RunSQL in the initial migration,
        # using jsonb_array_length(evidence_refs) > 0 which cannot be expressed via Django Q().
        # Domain-level enforcement is in ChatMessage._validate_invariant() (domain/entities.py).

    def __str__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.role}: {content_preview}"
