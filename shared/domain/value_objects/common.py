"""Common value objects for domain layer.

Pure Python dataclasses with no Django ORM dependency.
"""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TenantId:
    """Tenant identifier value object."""
    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("TenantId must be a non-empty string")


@dataclass(frozen=True)
class WorkspaceId:
    """Workspace identifier value object."""
    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise ValueError("WorkspaceId must be a UUID")


@dataclass(frozen=True)
class Email:
    """Email value object with validation."""
    value: str

    def __post_init__(self) -> None:
        if '@' not in self.value or '.' not in self.value.split('@')[1]:
            raise ValueError(f"Invalid email format: {self.value}")

    @property
    def local_part(self) -> str:
        """Get local part before @."""
        return self.value.split('@')[0]

    @property
    def domain(self) -> str:
        """Get domain part after @."""
        return self.value.split('@')[1]


@dataclass(frozen=True)
class SHA256Hash:
    """SHA-256 hash value object."""
    value: str

    def __post_init__(self) -> None:
        if len(self.value) != 64:
            raise ValueError("SHA-256 hash must be 64 hexadecimal characters")
        try:
            int(self.value, 16)
        except ValueError:
            raise ValueError("SHA-256 hash must be hexadecimal")


@dataclass(frozen=True)
class FileSize:
    """File size value object."""
    bytes: int

    def __post_init__(self) -> None:
        if self.bytes < 0:
            raise ValueError("File size cannot be negative")

    @property
    def kilobytes(self) -> float:
        """Size in KB."""
        return self.bytes / 1024

    @property
    def megabytes(self) -> float:
        """Size in MB."""
        return self.bytes / (1024 * 1024)

    def to_human_readable(self) -> str:
        """Human-readable representation."""
        if self.bytes < 1024:
            return f"{self.bytes} B"
        elif self.bytes < 1024 * 1024:
            return f"{self.kilobytes:.2f} KB"
        else:
            return f"{self.megabytes:.2f} MB"
