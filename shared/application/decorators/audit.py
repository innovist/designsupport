"""@audit decorator for use-case level audit logging.

REQ-01-AUDIT-001..003: Wraps execute() to record an AuditLog entry
inside the same DB transaction as the use-case work.

Usage:
    @audit("design_session.create", target_type_extractor=lambda kw: "DesignSession")
    class CreateSessionUseCase:
        async def execute(self, ...):
            ...
"""
from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Callable, Optional, Set

from django.db import transaction

from apps.audit_logs.application.dtos import AuditLogEntryDTO
from apps.audit_logs.application.ports import AuditLogRepositoryPort
from apps.audit_logs.infrastructure.repositories.audit_log_repository import (
    DjangoAuditLogRepository,
)
import logging

logger = logging.getLogger(__name__)

# Keys to redact from payload before digest computation
_REDACT_KEYS: Set[str] = {"password", "secret", "token", "access_token", "refresh_token"}


def _redact(data: dict) -> dict:
    """Return a shallow copy with sensitive keys replaced by '<redacted>'."""
    return {
        k: "<redacted>" if k.lower() in _REDACT_KEYS else v
        for k, v in data.items()
    }


def _compute_digest(kwargs: dict) -> str:
    """Compute SHA-256 digest of canonicalized (sorted-key) JSON of kwargs.

    Args:
        kwargs: Use-case keyword arguments (after redaction)

    Returns:
        Hex-encoded SHA-256 digest string
    """
    redacted = _redact(kwargs)
    canonical = json.dumps(redacted, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _get_repository() -> AuditLogRepositoryPort:
    return DjangoAuditLogRepository()


def audit(
    action_type: str,
    *,
    target_type_extractor: Callable[..., str] = lambda **kw: "unknown",
    target_id_extractor: Callable[..., str] = lambda **kw: "",
    record_failures: bool = False,
) -> Callable:
    """Class decorator that wraps execute() with audit logging.

    The decorator:
    1. Calls the original execute() inside django.db.transaction.atomic()
    2. On success: appends an AuditLogEntryDTO post-success
    3. On failure (if record_failures=True): appends a failed:<action_type> entry
       then re-raises
    4. Reads actor_id / tenant_id / workspace_id from TenantContext

    Args:
        action_type: Dot-separated action string, e.g. "accounts.authenticate"
        target_type_extractor: Callable(**kwargs) -> str for target_type
        target_id_extractor: Callable(**kwargs) -> str for target_id
        record_failures: When True, record a failed:<action_type> entry on exception

    Returns:
        Class decorator
    """
    # @MX:ANCHOR: [AUTO] audit() decorator wraps every audited use case execute()
    # @MX:REASON: fan_in >= 3; applied to authenticate, register_user, update_profile, and session use cases

    def decorator(cls):
        original_execute = cls.execute

        if _is_async_function(original_execute):
            @functools.wraps(original_execute)
            async def wrapped_execute_async(self, *args, **kwargs):
                from shared.infrastructure.tenant_middleware.middleware import TenantContext

                repo = _get_repository()
                tenant_id, workspace_id, actor_id = TenantContext.get()

                payload_digest = _compute_digest(dict(kwargs))
                target_type = target_type_extractor(**kwargs)
                target_id = target_id_extractor(**kwargs)

                _action = action_type
                if actor_id is None:
                    _action = f"system:{action_type}"

                try:
                    # Run use case + audit append inside one atomic block.
                    # Django's transaction.atomic() is synchronous; use sync_to_async
                    # to run it in async context without SynchronousOnlyOperation.
                    from asgiref.sync import sync_to_async

                    @sync_to_async
                    def _run():
                        with transaction.atomic():
                            entry = AuditLogEntryDTO(
                                actor_id=actor_id,
                                tenant_id=str(tenant_id) if tenant_id else None,
                                workspace_id=workspace_id,
                                action_type=_action,
                                target_type=target_type,
                                target_id=target_id,
                                payload_digest=payload_digest,
                            )
                            repo.append(entry)
                            return None

                    # Execute use case (already async)
                    result = await original_execute(self, *args, **kwargs)

                    # Append audit log within transaction
                    await _run()

                    return result
                except Exception:
                    if record_failures:
                        _try_record_failure(
                            repo, actor_id, tenant_id, workspace_id,
                            action_type, target_type, target_id, payload_digest,
                        )
                    raise

        else:
            @functools.wraps(original_execute)
            def wrapped_execute_sync(self, *args, **kwargs):
                from shared.infrastructure.tenant_middleware.middleware import TenantContext

                repo = _get_repository()
                tenant_id, workspace_id, actor_id = TenantContext.get()

                payload_digest = _compute_digest(dict(kwargs))
                target_type = target_type_extractor(**kwargs)
                target_id = target_id_extractor(**kwargs)

                _action = action_type
                if actor_id is None:
                    _action = f"system:{action_type}"

                try:
                    with transaction.atomic():
                        result = original_execute(self, *args, **kwargs)
                        entry = AuditLogEntryDTO(
                            actor_id=actor_id,
                            tenant_id=str(tenant_id) if tenant_id else None,
                            workspace_id=workspace_id,
                            action_type=_action,
                            target_type=target_type,
                            target_id=target_id,
                            payload_digest=payload_digest,
                        )
                        repo.append(entry)
                    return result
                except Exception as exc:
                    if record_failures:
                        _try_record_failure(
                            repo, actor_id, tenant_id, workspace_id,
                            action_type, target_type, target_id, payload_digest,
                        )
                    raise

        cls.execute = wrapped_execute_async if _is_async_function(original_execute) else wrapped_execute_sync
        return cls

    return decorator


def _is_async_function(fn: Any) -> bool:
    import inspect
    return inspect.iscoroutinefunction(fn)


def _try_record_failure(
    repo: AuditLogRepositoryPort,
    actor_id: Any,
    tenant_id: Any,
    workspace_id: Any,
    action_type: str,
    target_type: str,
    target_id: str,
    payload_digest: str,
) -> None:
    """Best-effort failure recording — never raises."""
    try:
        entry = AuditLogEntryDTO(
            actor_id=actor_id,
            tenant_id=str(tenant_id) if tenant_id else None,
            workspace_id=workspace_id,
            action_type=f"failed:{action_type}",
            target_type=target_type,
            target_id=target_id,
            payload_digest=payload_digest,
        )
        with transaction.atomic():
            repo.append(entry)
    except Exception:  # noqa: BLE001
        logger.warning("Failed to record failure audit entry for %s", action_type)
