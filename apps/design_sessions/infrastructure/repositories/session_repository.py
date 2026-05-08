"""Django ORM repository for DesignSession aggregate."""
from typing import List, Optional
from uuid import UUID

from asgiref.sync import sync_to_async

from apps.design_sessions.application.ports import SessionRepositoryPort
from apps.design_sessions.domain.entities import DesignSession, PipelineStep, SessionMode, SessionStatus
from apps.design_sessions.infrastructure.orm import models as orm


class DjangoSessionRepository(SessionRepositoryPort):
    """Django ORM implementation of SessionRepositoryPort.

    Uses select_for_update() inside transitions to prevent concurrent modifications.
    """

    async def get_by_id(self, session_id: UUID) -> Optional[DesignSession]:
        try:
            obj = await orm.DesignSession.all_objects.aget(id=session_id)
            return self._to_entity(obj)
        except orm.DesignSession.DoesNotExist:
            return None

    async def get_by_id_for_update(self, session_id: UUID) -> Optional[DesignSession]:
        """Get session with row lock for transition operations."""
        from django.db import transaction

        @sync_to_async
        def _get():
            with transaction.atomic():
                try:
                    return orm.DesignSession.all_objects.select_for_update().get(id=session_id)
                except orm.DesignSession.DoesNotExist:
                    return None

        obj = await _get()
        return self._to_entity(obj) if obj else None

    async def list_by_workspace(self, workspace_id: UUID) -> List[DesignSession]:
        objs = orm.DesignSession.all_objects.filter(workspace_id=workspace_id)
        results = []
        async for obj in objs:
            results.append(self._to_entity(obj))
        return results

    async def list_by_project(self, project_id: UUID) -> List[DesignSession]:
        objs = orm.DesignSession.all_objects.filter(project_id=project_id)
        results = []
        async for obj in objs:
            results.append(self._to_entity(obj))
        return results

    async def save(self, session: DesignSession) -> DesignSession:
        tenant_id = getattr(session, "tenant_id", "")
        workspace_id = getattr(session, "workspace_id", None)

        defaults = {
            "project_id": session.project_id,
            "mode": session.mode.value,
            "status": session.status.value,
            "current_step": session.current_step.value,
            "version": session.version,
            "started_by": session.started_by,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
        }
        obj, _ = await orm.DesignSession.all_objects.aupdate_or_create(
            id=session.id,
            defaults=defaults,
        )
        return self._to_entity(obj)

    @staticmethod
    def _to_entity(obj: orm.DesignSession) -> DesignSession:
        session = DesignSession(
            project_id=obj.project_id,
            started_by=obj.started_by,
            mode=SessionMode(obj.mode),
            status=SessionStatus(obj.status),
            current_step=PipelineStep(obj.current_step),
            version=obj.version,
            id=obj.id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
        session.tenant_id = obj.tenant_id  # type: ignore[attr-defined]
        session.workspace_id = obj.workspace_id  # type: ignore[attr-defined]
        return session
