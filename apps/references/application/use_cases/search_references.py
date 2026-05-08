"""Search references use case.

Calls multiple providers in parallel, merges results, applies license risk evaluation,
enforces thumbnail constraints, and clusters by taxonomy.
"""
from logging import getLogger
from typing import Any

from apps.references.application.dtos import (
    ReferenceSearchRequest,
    ReferenceSearchResponse,
)
from apps.references.domain.services import LicenseRiskEvaluator, ReferenceClusterer
from shared.domain.exceptions import ValidationError

logger = getLogger(__name__)


class SearchReferencesUseCase:
    """Search reference assets across multiple providers."""

    def __init__(
        self,
        adapter_registry: dict[str, Any],  # Provider name -> adapter
        license_evaluator: LicenseRiskEvaluator,
        clusterer: ReferenceClusterer,
        thumbnail_processor: Any,  # ThumbnailProcessor
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            adapter_registry: Registry of image search adapters
            license_evaluator: Service for license risk assessment
            clusterer: Service for taxonomy clustering
            thumbnail_processor: Service for thumbnail processing
        """
        self._adapter_registry = adapter_registry
        self._license_evaluator = license_evaluator
        self._clusterer = clusterer
        self._thumbnail_processor = thumbnail_processor

    async def execute(self, request: ReferenceSearchRequest) -> ReferenceSearchResponse:
        """Search for reference assets across providers.

        Args:
            request: Search request with query kind and payload

        Returns:
            Search response with clustered results and metadata

        Raises:
            ValidationError: If request is invalid
            OperationError: If all providers fail
        """
        # Validate request
        if not request.query_kind:
            raise ValidationError(field="query_kind", message="query_kind is required")

        if request.query_kind == "keyword" and not request.payload.get("query"):
            raise ValidationError(
                field="payload.query",
                message="query is required for keyword search",
            )

        logger.info(f"Searching references: kind={request.query_kind}, domain={request.domain}")

        try:
            all_results = []
            providers_used = []
            quota_remaining = {}

            # Dispatch based on query kind
            if request.query_kind == "keyword":
                # Parallel search across providers
                import asyncio

                search_tasks = []
                for provider_name, adapter in self._adapter_registry.items():
                    if hasattr(adapter, "search"):
                        task = self._search_single_provider(
                            provider_name,
                            adapter,
                            request.payload["query"],
                            request.max_results or 20,
                        )
                        search_tasks.append(task)

                # Execute in parallel
                provider_results = await asyncio.gather(*search_tasks, return_exceptions=True)

                # Collect successful results
                for result in provider_results:
                    if isinstance(result, Exception):
                        logger.warning(f"Provider search failed: {result}")
                        continue
                    if isinstance(result, dict):
                        all_results.extend(result["results"])
                        providers_used.append(result["provider"])
                        quota_remaining[result["provider"]] = result.get("quota_remaining", 0)

            elif request.query_kind == "by_image":
                # Image similarity search (single provider)
                provider_name = request.payload.get("provider", "unsplash")
                adapter = self._adapter_registry.get(provider_name)

                if adapter and hasattr(adapter, "search"):
                    # Use search() with image_url in options
                    result = await adapter.search(
                        query="",  # Empty query for image search
                        count=request.max_results or 20,
                        options={"image_url": request.payload.get("image_url")},
                    )
                    all_results.extend(result)
                    providers_used.append(provider_name)

            # Check for insufficient evidence
            if not all_results:
                logger.info(f"No results found for request: {request.query_kind}")
                return ReferenceSearchResponse(
                    results=[],
                    clusters=[],
                    total=0,
                    providers_used=[],
                    quota_remaining={},
                    insufficient_evidence=True,
                )

            # Process thumbnails and evaluate license risk
            processed_results = []
            for asset in all_results[: request.max_results or 20]:
                # Convert NormalizedReferenceCard to dict for processing
                if hasattr(asset, "provider"):
                    # It's a NormalizedReferenceCard dataclass
                    asset_dict = {
                        "provider": asset.provider,
                        "source_url": asset.source_url,
                        "thumbnail_url": asset.thumbnail_url,
                        "license_id": asset.license_id,
                    }
                else:
                    asset_dict = asset

                # Apply thumbnail constraints
                if asset_dict.get("thumbnail_url"):
                    asset_dict = await self._thumbnail_processor.process_asset(asset_dict)

                # Evaluate license risk
                license_id = asset_dict.get("license_id", "unknown")
                risk_level = self._license_evaluator.evaluate(license_id)
                asset_dict["license_risk"] = risk_level

                processed_results.append(asset_dict)

            # Cluster results by domain
            clusters = self._clusterer.cluster_by_domain(processed_results)

            logger.info(
                f"Search complete: {len(processed_results)} results, "
                f"{len(clusters)} clusters, providers={providers_used}"
            )

            return ReferenceSearchResponse(
                results=processed_results,
                clusters=clusters,
                total=len(processed_results),
                providers_used=providers_used,
                quota_remaining=quota_remaining,
                insufficient_evidence=False,
            )

        except Exception as e:
            logger.error(f"Reference search failed: {e}")
            raise

    async def _search_single_provider(
        self,
        provider_name: str,
        adapter: Any,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        """Search a single provider and handle errors.

        Args:
            provider_name: Name of the provider
            adapter: Provider adapter instance
            query: Search query
            max_results: Maximum results to return

        Returns:
            Dict with results, provider name, and quota info
        """
        try:
            results = await adapter.search(
                query=query,
                count=max_results,
            )
            return {
                "provider": provider_name,
                "results": results,
                "quota_remaining": getattr(adapter, "get_quota_remaining", lambda: 0)(),
            }
        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {e}")
            raise
