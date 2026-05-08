"""Domain exceptions for the application."""


# @MX:ANCHOR: Base domain exception used across all modules
# @MX:REASON: All domain errors inherit from this; provides structured error context
class DomainError(Exception):
    """Base exception for domain errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# @MX:ANCHOR: Standard not-found error across all repositories
# @MX:REASON: High fan-in; used by all domain repositories for missing entities
class NotFoundError(DomainError):
    """Raised when a requested entity is not found."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        self.entity_type = entity_type
        self.identifier = identifier
        message = f"{entity_type} with identifier '{identifier}' not found"
        super().__init__(message, {"entity_type": entity_type, "identifier": identifier})


class PermissionDeniedError(DomainError):
    """Raised when user lacks permission for an action."""

    def __init__(self, action: str, resource: str) -> None:
        self.action = action
        self.resource = resource
        message = f"Permission denied: {action} on {resource}"
        super().__init__(message, {"action": action, "resource": resource})


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"Validation failed for {field}: {message}", {"field": field})


class TenantIsolationError(DomainError):
    """Raised when tenant isolation is violated."""

    def __init__(self, tenant_id: str, resource: str) -> None:
        self.tenant_id = tenant_id
        self.resource = resource
        message = f"Tenant isolation violation: tenant {tenant_id} accessing {resource}"
        super().__init__(message, {"tenant_id": tenant_id, "resource": resource})


class InvariantViolationError(DomainError):
    """Raised when a domain invariant is violated."""

    def __init__(self, invariant: str, details: dict | None = None) -> None:
        self.invariant = invariant
        message = f"Domain invariant violated: {invariant}"
        super().__init__(message, details)


class StateTransitionError(DomainError):
    """Raised when invalid state transition is attempted."""

    def __init__(self, current_state: str, target_state: str) -> None:
        self.current_state = current_state
        self.target_state = target_state
        message = f"Invalid state transition: {current_state} -> {target_state}"
        super().__init__(
            message,
            {"current_state": current_state, "target_state": target_state}
        )


# @MX:ANCHOR: Infrastructure operation error for external system failures
# @MX:REASON: Used by all adapters/repositories for external API call failures
class OperationError(DomainError):
    """Raised when an infrastructure operation fails."""

    def __init__(self, operation: str, reason: str) -> None:
        self.operation = operation
        self.reason = reason
        message = f"Operation failed: {operation} - {reason}"
        super().__init__(message, {"operation": operation, "reason": reason})
