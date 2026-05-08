"""References value objects.

Immutable value objects for references domain.
"""
from dataclasses import dataclass
from enum import Enum


class ReferenceKind(Enum):
    """Reference asset kind types."""

    IMAGE = "image"
    DOCUMENT = "document"
    INTERNAL = "internal"
    WEB_PAGE = "web_page"


class QueryKind(Enum):
    """Reference query types.

    keyword: Text-based keyword search
    image: Visual similarity search using image
    sketch: Sketch-based search (shape/structure focused)
    document: Document-based search
    internal: Internal asset search
    expanded: OpenDeepSearch pattern (search → rerank → extract)
    """

    KEYWORD = "keyword"
    IMAGE = "image"
    SKETCH = "sketch"
    DOCUMENT = "document"
    INTERNAL = "internal"
    EXPANDED = "expanded"


class Tier(Enum):
    """Image provider tier classification.

    Tier 1: Direct use (11 providers, low license risk)
    Tier 2: License verification required (3 providers, medium risk)
    Tier 3: Link-only, abstraction forced (4 providers, high risk)
    """

    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class LicenseRisk(Enum):
    """License risk level.

    low: CC0, CC-BY, Public Domain - safe for most uses
    medium: CC-BY-SA, CC-BY-NC - some restrictions
    high: Proprietary, unknown - abstraction only (no direct style apply)
    unknown: Risk not yet assessed
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ThumbnailSpec:
    """Thumbnail specification value object.

    Enforces thumbnail constraints for storage optimization.
    Max edge is 1024px, format is WebP, quality is 80%.

    Attributes:
        max_edge: Maximum edge length in pixels (must be <= 1024)
        format: Image format (always "webp")
        quality: Compression quality (0-100)
    """

    max_edge: int = 1024
    format: str = "webp"
    quality: int = 80

    def __post_init__(self):
        """Validate thumbnail specification."""
        if self.max_edge > 1024:
            raise ValueError(
                f"Thumbnail max edge must be <= 1024px, got {self.max_edge}"
            )
        if self.format != "webp":
            raise ValueError(f"Thumbnail format must be webp, got {self.format}")
        if not 0 <= self.quality <= 100:
            raise ValueError(f"Quality must be 0-100, got {self.quality}")
