"""References domain services.

Business logic services for reference analysis and evaluation.
"""


# @MX:ANCHOR: [AUTO] License risk classification for IP compliance
# @MX:REASON: Determines abstraction-only usage; critical for legal compliance
# @MX:SPEC: REQ-02-REF-005, REQ-02-REF-013
class LicenseRiskEvaluator:
    """Evaluate license risk from license_id.

    Rules from SPEC-02 REQ-02-REF-005/013:
    - CC0, CC-BY, Public Domain → low
    - CC-BY-SA, CC-BY-NC → medium
    - Proprietary, no license meta, unknown → high (abstraction_only=true)
    """

    # Mapping of license IDs to risk levels
    _RISK_MAPPING = {
        # Low risk - permissive licenses
        "CC0": "low",
        "cc0": "low",
        "public-domain": "low",
        "CC-BY": "low",
        "cc-by": "low",
        "pdm": "low",
        # Medium risk - share-alike or non-commercial
        "CC-BY-SA": "medium",
        "cc-by-sa": "medium",
        "CC-BY-NC": "medium",
        "cc-by-nc": "medium",
        "CC-BY-NC-SA": "medium",
        "cc-by-nc-sa": "medium",
        # High risk - all rights reserved or unknown
        "all-rights-reserved": "high",
        "copyright": "high",
        "proprietary": "high",
        # Unknown - treat as high risk
        "unknown": "high",
        "": "high",
    }

    def evaluate(self, license_id: str) -> str:
        """Evaluate license risk level.

        Args:
            license_id: SPDX or provider license identifier

        Returns:
            Risk level: "low", "medium", "high", or "unknown"
        """
        # Normalize license ID
        normalized = license_id.strip().lower()

        # Look up in mapping
        risk = self._RISK_MAPPING.get(normalized, "high")

        return risk

    def requires_abstraction_only(self, license_id: str) -> bool:
        """Check if license requires abstraction-only usage.

        Returns True for high-risk licenses.
        """
        risk = self.evaluate(license_id)
        return risk == "high"


# @MX:NOTE: [AUTO] Thumbnail constraints enforce storage optimization
# @MX:REASON: Max 1024px edge and WebP format reduce storage costs; no high-res originals stored
# @MX:SPEC: REQ-02-REF-010, REQ-02-REF-012
class ThumbnailGenerator:
    """Thumbnail generation and validation.

    Validates thumbnail constraints per SPEC-02 REQ-02-REF-010/012:
    - Max edge <= 1024px
    - WebP format
    - No original high-res storage
    """

    def validate_dimensions(self, width: int, height: int) -> bool:
        """Validate thumbnail dimensions.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            True if dimensions are valid (max edge <= 1024)
        """
        max_edge = max(width, height)
        return max_edge <= 1024

    def validate_format(self, format: str) -> bool:
        """Validate thumbnail format.

        Args:
            format: Image format (webp, jpg, png, etc.)

        Returns:
            True if format is WebP
        """
        return format.lower() == "webp"

    def calculate_scaling(
        self,
        original_width: int,
        original_height: int,
        target_max_edge: int = 1024,
    ) -> tuple[int, int]:
        """Calculate scaled dimensions maintaining aspect ratio.

        Args:
            original_width: Original image width
            original_height: Original image height
            target_max_edge: Target maximum edge (default 1024)

        Returns:
            Tuple of (scaled_width, scaled_height)
        """
        max_edge = max(original_width, original_height)

        # If already within bounds, return original
        if max_edge <= target_max_edge:
            return original_width, original_height

        # Calculate scale factor
        scale_factor = target_max_edge / max_edge

        # Calculate new dimensions
        scaled_width = int(original_width * scale_factor)
        scaled_height = int(original_height * scale_factor)

        return scaled_width, scaled_height


# @MX:ANCHOR: [AUTO] Multi-provider quota management with round-robin fallback
# @MX:REASON: Prevents API rate limiting; ensures service availability across providers
# @MX:SPEC: REQ-02-REF-016
class ProviderQuotaManager:
    """Manage provider quotas with round-robin fallback.

    Implements SPEC-02 REQ-02-REF-016:
    - Track daily limits per provider
    - Round-robin to other providers on exhaustion
    - Return "quota exceeded" when all providers exhausted
    """

    def __init__(self):
        """Initialize quota manager."""
        self._providers = {}

    def register_provider(
        self,
        provider: str,
        daily_limit: int,
        used_today: int = 0,
        active: bool = True,
    ) -> None:
        """Register a provider with quota limits.

        Args:
            provider: Provider name
            daily_limit: Daily call limit
            used_today: Calls used today
            active: Whether provider is active
        """
        self._providers[provider] = {
            "daily_limit": daily_limit,
            "used_today": used_today,
            "active": active,
        }

    def get_available_provider(self, preferred_tier: list[str]) -> str | None:
        """Get next available provider with quota remaining.

        Args:
            preferred_tier: List of preferred providers in order

        Returns:
            Provider name or None if all exhausted

        Implements round-robin: try providers in order, skip exhausted ones.
        """
        for provider in preferred_tier:
            if provider not in self._providers:
                continue

            quota = self._providers[provider]
            if not quota["active"]:
                continue

            if quota["used_today"] < quota["daily_limit"]:
                return provider

        return None

    def record_usage(self, provider: str) -> bool:
        """Record API usage for a provider.

        Args:
            provider: Provider name

        Returns:
            True if usage recorded, False if provider not found or quota exceeded
        """
        if provider not in self._providers:
            return False

        quota = self._providers[provider]
        if quota["used_today"] >= quota["daily_limit"]:
            return False

        quota["used_today"] += 1
        return True

    def is_quota_exceeded(self, provider: str) -> bool:
        """Check if provider quota is exceeded.

        Args:
            provider: Provider name

        Returns:
            True if quota exceeded or provider inactive
        """
        if provider not in self._providers:
            return True

        quota = self._providers[provider]
        return not quota["active"] or quota["used_today"] >= quota["daily_limit"]


class ReferenceClusterer:
    """Cluster reference search results by style, category, and domain.

    Implements SPEC-02 REQ-02-REF-007/008/009:
    - Cluster by visual similarity (style tags)
    - Cluster by semantic category (domain tags)
    - Return labeled clusters for UI rendering
    """

    def __init__(self):
        """Initialize clusterer."""
        pass

    def cluster_by_style(self, references: list[dict]) -> list[dict]:
        """Cluster references by visual style.

        Args:
            references: List of reference dictionaries

        Returns:
            List of cluster dictionaries with label and assets
        """
        # Simple implementation - cluster by style tags
        clusters = {}
        for ref in references:
            style_tags = ref.get("style_tags", [])
            if not style_tags:
                style = "uncategorized"
            else:
                style = style_tags[0]  # Use first style tag as cluster key

            if style not in clusters:
                clusters[style] = {
                    "label": style.title(),
                    "category": "style",
                    "assets": [],
                }
            clusters[style]["assets"].append(ref)

        return list(clusters.values())

    def cluster_by_domain(self, references: list[dict]) -> list[dict]:
        """Cluster references by domain tags.

        Args:
            references: List of reference dictionaries

        Returns:
            List of cluster dictionaries with label and assets
        """
        clusters = {}
        for ref in references:
            domain_tags = ref.get("domain_tags", [])
            if not domain_tags:
                domain = "general"
            else:
                domain = domain_tags[0]  # Use first domain tag as cluster key

            if domain not in clusters:
                clusters[domain] = {
                    "label": domain.title(),
                    "category": "domain",
                    "assets": [],
                }
            clusters[domain]["assets"].append(ref)

        return list(clusters.values())

    def cluster_all(self, references: list[dict]) -> dict:
        """Cluster references by both style and domain.

        Args:
            references: List of reference dictionaries

        Returns:
            Dictionary with style_clusters and domain_clusters
        """
        return {
            "style_clusters": self.cluster_by_style(references),
            "domain_clusters": self.cluster_by_domain(references),
        }
