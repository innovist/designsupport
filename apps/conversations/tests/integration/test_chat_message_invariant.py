"""Integration tests for INV-01-03: AI messages must have evidence_refs or is_hypothesis."""
import pytest
from uuid import uuid4

from apps.conversations.domain.entities import ChatMessage, MessageRole
from shared.domain.exceptions import InvariantViolationError


class TestChatMessageInvariant:
    def _conv_id(self):
        return uuid4()

    def test_ai_message_without_evidence_raises(self):
        with pytest.raises(InvariantViolationError) as exc_info:
            ChatMessage(
                conversation_id=self._conv_id(),
                role=MessageRole.ASSISTANT,
                content="Here is my analysis.",
                evidence_refs=[],
                is_hypothesis=False,
            )
        assert "INV-01-03" in str(exc_info.value)

    def test_system_message_without_evidence_raises(self):
        with pytest.raises(InvariantViolationError):
            ChatMessage(
                conversation_id=self._conv_id(),
                role=MessageRole.SYSTEM,
                content="System prompt.",
                evidence_refs=None,
                is_hypothesis=False,
            )

    def test_ai_message_with_evidence_ok(self):
        msg = ChatMessage(
            conversation_id=self._conv_id(),
            role=MessageRole.ASSISTANT,
            content="Based on evidence.",
            evidence_refs=[{"source": "doc1", "page": 3}],
            is_hypothesis=False,
        )
        assert msg.role == MessageRole.ASSISTANT
        assert len(msg.evidence_refs) == 1

    def test_ai_message_with_is_hypothesis_ok(self):
        msg = ChatMessage(
            conversation_id=self._conv_id(),
            role=MessageRole.ASSISTANT,
            content="This is a hypothesis.",
            evidence_refs=[],
            is_hypothesis=True,
        )
        assert msg.is_hypothesis is True

    def test_user_message_without_evidence_ok(self):
        msg = ChatMessage(
            conversation_id=self._conv_id(),
            role=MessageRole.USER,
            content="Hello.",
            evidence_refs=[],
            is_hypothesis=False,
        )
        assert msg.role == MessageRole.USER
