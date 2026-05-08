"""References domain invariants.

Business rules and constraints that must always hold.
These invariants are enforced at domain boundaries.
"""


class ReferenceInvariantViolation(Exception):
    """Raised when a reference invariant is violated."""

    pass


def enforce_thumbnail_max_1024(thumbnail_max_edge_px: int) -> None:
    """Enforce INV-02-05: thumbnail max edge <= 1024px.

    Args:
        thumbnail_max_edge_px: Maximum edge dimension in pixels

    Raises:
        ReferenceInvariantViolation: If constraint violated
    """
    if thumbnail_max_edge_px > 1024:
        raise ReferenceInvariantViolation(
            f"Thumbnail max edge must be <= 1024px, got {thumbnail_max_edge_px}"
        )


def enforce_high_license_risk_abstraction_only(
    license_risk: str,
    direct_style_apply: bool,
) -> None:
    """Enforce INV-02-03 + INV-02-06: high license risk forces abstraction only.

    Args:
        license_risk: License risk level
        direct_style_apply: Whether direct style apply is requested

    Raises:
        ReferenceInvariantViolation: If constraint violated
    """
    if license_risk == "high" and direct_style_apply:
        raise ReferenceInvariantViolation(
            f"High license risk ({license_risk}) forbids direct style application. "
            "Use abstraction-only mode."
        )


def enforce_no_original_high_res_storage(
    thumbnail_uri: str,
    original_uri: str | None,
) -> None:
    """Enforce INV-02-05: only thumbnails stored, no originals.

    Args:
        thumbnail_uri: Thumbnail storage URI
        original_uri: Original file storage URI (should be None)

    Raises:
        ReferenceInvariantViolation: If original file is stored
    """
    if original_uri is not None:
        raise ReferenceInvariantViolation(
            f"Original high-res file storage is forbidden. "
            f"Only thumbnails (max 1024px) should be stored. "
            f"Got original_uri: {original_uri}"
        )


def validate_tier_3_direct_style_apply(tier: int, direct_style_apply: bool) -> None:
    """Enforce INV-02-06: Tier 3 assets cannot have direct_style_apply.

    Args:
        tier: Provider tier (1, 2, or 3)
        direct_style_apply: Whether direct style apply is requested

    Raises:
        ReferenceInvariantViolation: If constraint violated
    """
    if tier == 3 and direct_style_apply:
        raise ReferenceInvariantViolation(
            f"Tier 3 assets cannot have direct_style_apply=True. "
            f"Tier 3 requires abstraction-only usage."
        )
