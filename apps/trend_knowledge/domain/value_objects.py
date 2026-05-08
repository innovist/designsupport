"""Trend Knowledge value objects.

Immutable value objects for trend domain.
"""
from dataclasses import dataclass
from enum import Enum


class TrustLevel(Enum):
    """Source trust level rating."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ParseStatus(Enum):
    """Document parsing status.

    pending: Not yet parsed
    parsing: Currently being parsed
    parsed: Successfully parsed
    failed: Parsing failed
    """

    PENDING = "pending"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"


class LicenseType(Enum):
    """Content license types.

    creative_commons: Various CC licenses (CC-BY, CC-BY-SA, etc.)
    public_domain: Public domain (CC0, PD)
    proprietary: All rights reserved
    unknown: License information not available
    """

    CREATIVE_COMMONS = "creative_commons"
    PUBLIC_DOMAIN = "public_domain"
    PROPRIETARY = "proprietary"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CrawlSchedule:
    """Crawl schedule value object.

    Encapsulates cron expression for scheduled crawling.
    """

    cron_expression: str

    def __post_init__(self):
        """Validate cron expression format."""
        # Basic validation: 5 parts separated by spaces
        parts = self.cron_expression.split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression: {self.cron_expression}. "
                "Must have 5 parts: minute hour day month weekday"
            )


@dataclass(frozen=True)
class ConfidenceScore:
    """Confidence score value object.

    Represents confidence in an insight or claim (0.0 to 1.0).
    """

    value: float

    def __post_init__(self):
        """Validate confidence score range."""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(
                f"Confidence score must be between 0.0 and 1.0, got {self.value}"
            )

    def is_high(self) -> bool:
        """Check if confidence is high (> 0.7)."""
        return self.value > 0.7

    def is_low(self) -> bool:
        """Check if confidence is low (< 0.4)."""
        return self.value < 0.4
