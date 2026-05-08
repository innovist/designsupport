"""Structured JSON logging with tenant/workspace/session context."""
import structlog
from typing import Any

logger = structlog.get_logger()


def get_logger(**kwargs: Any) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with context fields.

    Args:
        **kwargs: Context fields (tenant_id, workspace_id, session_id, step, etc.)

    Returns:
        BoundLogger with context
    """
    return logger.bind(**kwargs)


def log_with_context(
    message: str,
    level: str = 'info',
    **kwargs: Any,
) -> None:
    """Log a message with structured context.

    Args:
        message: Log message
        level: Log level (debug, info, warning, error)
        **kwargs: Context fields (tenant_id, workspace_id, session_id, step, etc.)
    """
    log = logger.bind(**kwargs)

    log_method = getattr(log, level, log.info)
    log_method(message)


class TenantLogger:
    """Logger that automatically includes tenant/workspace context."""

    def __init__(
        self,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Initialize logger with context."""
        self.context: dict[str, Any] = {}
        if tenant_id:
            self.context['tenant_id'] = tenant_id
        if workspace_id:
            self.context['workspace_id'] = workspace_id
        if session_id:
            self.context['session_id'] = session_id

    def bind(self, **kwargs: Any) -> 'TenantLogger':
        """Bind additional context."""
        new_context = self.context.copy()
        new_context.update(kwargs)
        new_logger = TenantLogger()
        new_logger.context = new_context
        return new_logger

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        log_with_context(message, level='debug', **{**self.context, **kwargs})

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        log_with_context(message, level='info', **{**self.context, **kwargs})

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        log_with_context(message, level='warning', **{**self.context, **kwargs})

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        log_with_context(message, level='error', **{**self.context, **kwargs})

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        log_with_context(message, level='critical', **{**self.context, **kwargs})


def get_tenant_logger(
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    session_id: str | None = None,
) -> TenantLogger:
    """Get a tenant-aware logger.

    Args:
        tenant_id: Tenant identifier
        workspace_id: Workspace identifier
        session_id: Session identifier

    Returns:
        TenantLogger instance
    """
    return TenantLogger(tenant_id=tenant_id, workspace_id=workspace_id, session_id=session_id)
