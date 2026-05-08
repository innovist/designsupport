"""Result types for use case returns.

Provides Either-like types for error handling without exceptions.
"""
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from shared.domain.exceptions import DomainError

T = TypeVar('T')
L = TypeVar('L', bound=DomainError)


@dataclass(frozen=True)
class Success:
    """Successful result of an operation."""
    value: Any

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False


@dataclass(frozen=True)
class Failure:
    """Failed result of an operation."""
    error: DomainError

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True


@dataclass
class Result(Generic[T]):
    """Result type for operations that can fail.

    Usage:
        result = Result.success(value)
        if result.is_failure:
            return result
        value = result.value

        result = Result.failure(error)
        return result
    """

    _value: T | None = None
    _error: DomainError | None = None

    @classmethod
    def success(cls, value: T) -> 'Result[T]':
        """Create a successful result."""
        return cls(_value=value, _error=None)

    @classmethod
    def failure(cls, error: DomainError) -> 'Result[T]':
        """Create a failed result."""
        return cls(_value=None, _error=error)

    @property
    def value(self) -> T:
        """Get the success value."""
        if self._error is not None:
            raise ValueError("Cannot get value from failed result")
        if self._value is None:
            raise ValueError("Result has no value")
        return self._value

    @property
    def error(self) -> DomainError | None:
        """Get the error if failed."""
        return self._error

    @property
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self._error is None

    @property
    def is_failure(self) -> bool:
        """Check if result is failed."""
        return self._error is not None

    def map(self, func) -> 'Result':
        """Apply function to value if success, else pass through error."""
        if self.is_failure:
            return self
        try:
            return Result.success(func(self.value))
        except Exception as e:
            return Result.failure(DomainError(str(e)))


@dataclass
class Either(Generic[L, T]):
    """Either type for returning left (error) or right (success).

    Usage:
        def divide(a: int, b: int) -> Either[ValidationError, int]:
            if b == 0:
                return Either.left(ValidationError("b", "Cannot divide by zero"))
            return Either.right(a // b)
    """

    _left: L | None = None
    _right: T | None = None

    @classmethod
    def left(cls, value: L) -> 'Either[L, T]':
        """Create a left (error) value."""
        return cls(_left=value, _right=None)

    @classmethod
    def right(cls, value: T) -> 'Either[L, T]':
        """Create a right (success) value."""
        return cls(_left=None, _right=value)

    @property
    def is_left(self) -> bool:
        """Check if this is a left value."""
        return self._left is not None

    @property
    def is_right(self) -> bool:
        """Check if this is a right value."""
        return self._right is not None

    def get_left(self) -> L:
        """Get left value."""
        if self._left is None:
            raise ValueError("Not a left value")
        return self._left

    def get_right(self) -> T:
        """Get right value."""
        if self._right is None:
            raise ValueError("Not a right value")
        return self._right

    def map(self, func) -> 'Either[L, Any]':
        """Apply function to right value if present."""
        if self.is_left:
            return self
        try:
            return Either.right(func(self.get_right()))
        except Exception as e:
            return Either.left(DomainError(str(e)))
