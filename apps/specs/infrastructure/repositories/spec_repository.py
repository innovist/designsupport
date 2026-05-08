"""Django repository implementation for specs module."""
from typing import Optional

from apps.specs.application.ports import DomainPackRepositoryPort, SpecDocumentRepositoryPort
from apps.specs.domain.entities import DomainPack, SpecDocument


class DjangoSpecDocumentRepository(SpecDocumentRepositoryPort):
    """Django ORM repository for SpecDocument."""

    async def save(self, spec: SpecDocument) -> SpecDocument:
        """Save a spec document."""
        from apps.specs.infrastructure.orm.models import SpecDocumentModel

        model = SpecDocumentModel.from_domain(spec)

        # Check if it's a new spec or update
        existing = await SpecDocumentModel.objects.filter(id=str(spec.id)).afirst()
        if existing:
            # Update existing
            model.id = existing.id
            model.save()
        else:
            # Create new
            model.save()

        return model.to_domain()

    async def get_by_id(self, spec_id):
        """Get spec by ID."""
        from apps.specs.infrastructure.orm.models import SpecDocumentModel

        model = await SpecDocumentModel.objects.filter(id=str(spec_id)).afirst()
        if not model:
            return None
        return model.to_domain()

    async def get_by_session(self, session_id) -> Optional[SpecDocument]:
        """Get latest approved spec for a session."""
        from apps.specs.infrastructure.orm.models import SpecDocumentModel

        model = (
            await SpecDocumentModel.objects.filter(
                session_id=str(session_id), status="approved"
            )
            .order_by("-version")
            .afirst()
        )
        if not model:
            return None
        return model.to_domain()

    async def list_all_versions(self, session_id) -> list[SpecDocument]:
        """List all versions of specs for a session."""
        from apps.specs.infrastructure.orm.models import SpecDocumentModel

        models = (
            SpecDocumentModel.objects.filter(session_id=str(session_id))
            .order_by("-version")
            .all()
        )
        return [m.to_domain() async for m in models]

    async def list_by_status(self, status: str) -> list[SpecDocument]:
        """List specs by status."""
        from apps.specs.infrastructure.orm.models import SpecDocumentModel

        models = SpecDocumentModel.objects.filter(status=status).order_by("-created_at")
        return [m.to_domain() async for m in models]


class DjangoDomainPackRepository(DomainPackRepositoryPort):
    """Django ORM repository for DomainPack."""

    async def get_by_id(self, pack_id: str) -> Optional[DomainPack]:
        """Get domain pack by ID."""
        from apps.specs.infrastructure.orm.models import DomainPackModel

        try:
            model = await DomainPackModel.objects.aget(id=pack_id)
            return model.to_domain()
        except DomainPackModel.DoesNotExist:
            return None

    async def list_all(self) -> list[DomainPack]:
        """List all domain packs."""
        from apps.specs.infrastructure.orm.models import DomainPackModel

        models = DomainPackModel.objects.all()
        return [m.to_domain() async for m in models]

    async def exists(self, pack_id: str) -> bool:
        """Check if domain pack exists."""
        from apps.specs.infrastructure.orm.models import DomainPackModel

        return await DomainPackModel.objects.filter(id=pack_id).aexists()
