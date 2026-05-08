"""Django ORM repository for Reference entities.

Implements repository ports for ReferenceAsset and ReferenceAnalysis.
"""
from logging import getLogger
from typing import Any
from uuid import UUID

logger = getLogger(__name__)


class DjangoReferenceRepository:
    """Django ORM repository for Reference entities."""

    async def save_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
        """Save a reference asset.

        Args:
            asset: Reference asset data

        Returns:
            Saved asset data

        Raises:
            RuntimeError: If Django models not available
        """
        try:
            from apps.references.models import ReferenceAsset as ReferenceAssetModel

            # Convert dict to model
            model_data = {
                "id": asset.get("id"),
                "provider": asset.get("provider"),
                "asset_type": asset.get("asset_type", "image"),
                "title": asset.get("title", ""),
                "description": asset.get("description"),
                "thumbnail_url": asset.get("thumbnail_url", ""),
                "original_url": asset.get("original_url", ""),
                "license": asset.get("license", {}),
                "attribution": asset.get("attribution"),
                "metadata": asset.get("metadata", {}),
            }

            # Create or update
            model, created = ReferenceAssetModel.objects.update_or_create(
                id=model_data["id"],
                defaults=model_data,
            )

            logger.info(f"Saved ReferenceAsset: {model.id} (created: {created})")

            return self._model_to_dict(model)

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            raise RuntimeError("Django models not available") from e

    async def get_asset_by_id(self, asset_id: str) -> dict[str, Any] | None:
        """Get asset by ID.

        Args:
            asset_id: Asset ID (string from external provider)

        Returns:
            Asset data or None
        """
        try:
            from apps.references.models import ReferenceAsset as ReferenceAssetModel

            model = ReferenceAssetModel.objects.filter(id=asset_id).first()
            if model:
                return self._model_to_dict(model)
            return None

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return None

    async def search_assets(
        self,
        query: str,
        asset_type: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search assets by query.

        Args:
            query: Search query
            asset_type: Optional asset type filter
            limit: Maximum results

        Returns:
            List of asset data
        """
        try:
            from apps.references.models import ReferenceAsset as ReferenceAssetModel
            from django.db.models import Q

            queryset = ReferenceAssetModel.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )

            if asset_type:
                queryset = queryset.filter(asset_type=asset_type)

            models = queryset[:limit]
            return [self._model_to_dict(m) for m in models]

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return []

    def _model_to_dict(self, model: Any) -> dict[str, Any]:
        """Convert Django model to dict.

        Args:
            model: Django ReferenceAsset model

        Returns:
            Asset data dict
        """
        return {
            "id": model.id,
            "provider": model.provider,
            "asset_type": model.asset_type,
            "title": model.title,
            "description": model.description,
            "thumbnail_url": model.thumbnail_url,
            "original_url": model.original_url,
            "license": model.license,
            "attribution": model.attribution,
            "metadata": model.metadata,
            "created_at": model.created_at.isoformat() if hasattr(model, "created_at") else None,
        }
