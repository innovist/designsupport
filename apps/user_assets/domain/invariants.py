"""User asset domain invariants.

Business rules for sketch immutability.
"""
from shared.domain.exceptions import InvariantViolationError


def sketch_immutability_invariant(
    original_uri: str,
    sha256: str,
    old_uri: str | None = None,
    old_sha256: str | None = None,
) -> None:
    """Enforce sketch immutability invariant.

    Original URI and SHA-256 must never change after creation.

    Args:
        original_uri: Current original URI
        sha256: Current SHA-256 hash
        old_uri: Previous original URI (for updates)
        old_sha256: Previous SHA-256 hash (for updates)

    Raises:
        InvariantViolationError: If immutable fields would change
    """
    if old_uri is not None and original_uri != old_uri:
        raise InvariantViolationError(
            "sketch_immutability",
            {"field": "original_uri", "old": old_uri, "new": original_uri},
        )

    if old_sha256 is not None and sha256 != old_sha256:
        raise InvariantViolationError(
            "sketch_immutability",
            {"field": "sha256", "old": old_sha256, "new": sha256},
        )
