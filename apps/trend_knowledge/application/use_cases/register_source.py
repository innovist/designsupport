"""Register trend source use case.

Validates source URLs via SSRF guard and creates TrendSource entities.
"""
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from apps.trend_knowledge.application.dtos import TrendSourceDTO
from apps.trend_knowledge.application.ports import (
    TrendSourceRepositoryPort,
)
from apps.trend_knowledge.domain.entities import TrendSource, TrendSourceType
from apps.trend_knowledge.domain.services import SSRFGuard
from shared.domain.exceptions import ValidationError


class RegisterTrendSourceUseCase:
    """Register a new trend source with URL validation."""

    def __init__(
        self,
        source_repository: TrendSourceRepositoryPort,
        ssrf_guard: SSRFGuard,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            source_repository: Repository for source persistence
            ssrf_guard: SSRF protection for URL validation
        """
        self._source_repository = source_repository
        self._ssrf_guard = ssrf_guard

    async def execute(
        self,
        url: str,
        source_type: TrendSourceType,
        domain: str,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> TrendSourceDTO:
        """Register a new trend source.

        Args:
            url: Source URL to validate and register
            source_type: Type of trend source (rss, api, scrape)
            domain: Domain category for the source
            name: Optional display name
            config: Optional source-specific configuration

        Returns:
            DTO of created TrendSource

        Raises:
            ValidationError: If URL fails SSRF guard validation
            ValueError: If URL is invalid or source_type is unknown
        """
        # Validate URL via SSRF guard
        is_safe, error_message = await self._ssrf_guard.validate_url(url)
        if not is_safe:
            raise ValidationError(
                f"URL validation failed: {error_message}",
                field="url",
                value=url,
            )

        # Generate display name if not provided
        if name is None:
            name = url

        # Create source entity
        source = TrendSource(
            id=uuid4(),
            url=url,
            source_type=source_type,
            domain=domain,
            name=name,
            config=config or {},
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Persist source
        saved_source = await self._source_repository.save(source)

        # Return DTO
        return TrendSourceDTO(
            id=str(saved_source.id),
            url=saved_source.url,
            source_type=saved_source.source_type.value,
            domain=saved_source.domain,
            name=saved_source.name,
            config=saved_source.config,
            is_active=saved_source.is_active,
            created_at=saved_source.created_at.isoformat(),
            updated_at=saved_source.updated_at.isoformat(),
        )
