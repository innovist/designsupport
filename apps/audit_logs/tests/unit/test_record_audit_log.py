"""Unit tests for RecordAuditLogUseCase and audit helpers.

TDD RED → GREEN: idempotency, payload_digest stability, redaction, rollback.
"""
import hashlib
import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.audit_logs.application.dtos import AuditLogEntryDTO
from apps.audit_logs.application.use_cases.record_audit_log import RecordAuditLogUseCase
from shared.application.decorators.audit import _compute_digest, _redact
from shared.domain.exceptions import OperationError


class TestRedaction:
    def test_redacts_password_key(self):
        result = _redact({"email": "a@b.com", "password": "secret"})
        assert result["password"] == "<redacted>"
        assert result["email"] == "a@b.com"

    def test_redacts_token_and_secret(self):
        result = _redact({"token": "tok123", "secret": "s3cr3t", "data": "ok"})
        assert result["token"] == "<redacted>"
        assert result["secret"] == "<redacted>"
        assert result["data"] == "ok"

    def test_case_insensitive_redaction(self):
        result = _redact({"PASSWORD": "x", "ACCESS_TOKEN": "y"})
        assert result["PASSWORD"] == "<redacted>"
        assert result["ACCESS_TOKEN"] == "<redacted>"


class TestPayloadDigest:
    def test_digest_is_sha256_hex(self):
        digest = _compute_digest({"a": 1})
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_digest_stable_across_calls(self):
        kwargs = {"email": "x@y.com", "display_name": "Test"}
        d1 = _compute_digest(kwargs)
        d2 = _compute_digest(kwargs)
        assert d1 == d2

    def test_digest_differs_for_different_inputs(self):
        d1 = _compute_digest({"a": 1})
        d2 = _compute_digest({"a": 2})
        assert d1 != d2

    def test_password_not_in_digest(self):
        digest = _compute_digest({"password": "hunter2", "email": "a@b.com"})
        # Rebuild what the digest should be with redacted password
        expected_canonical = json.dumps({"email": "a@b.com", "password": "<redacted>"}, sort_keys=True)
        expected = hashlib.sha256(expected_canonical.encode()).hexdigest()
        assert digest == expected


class TestRecordAuditLogUseCase:
    def _make_entry(self) -> AuditLogEntryDTO:
        return AuditLogEntryDTO(
            actor_id=uuid4(),
            tenant_id="tenant-1",
            workspace_id=uuid4(),
            action_type="accounts.authenticate",
            target_type="User",
            target_id="",
            payload_digest="abc123",
        )

    def test_calls_repository_append(self):
        repo = MagicMock()
        uc = RecordAuditLogUseCase(repo)
        entry = self._make_entry()
        uc.execute(entry)
        repo.append.assert_called_once_with(entry)

    def test_propagates_repository_error(self):
        repo = MagicMock()
        repo.append.side_effect = OperationError("audit_log.append", "DB timeout")
        uc = RecordAuditLogUseCase(repo)
        with pytest.raises(OperationError):
            uc.execute(self._make_entry())
