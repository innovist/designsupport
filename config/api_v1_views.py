"""Compatibility API for legacy user pages.

These endpoints read and mutate the same persisted domain models used by the
new spec APIs. They exist so older templates do not call dead /api/v1 routes.
"""
import os
from uuid import UUID, uuid4

from asgiref.sync import async_to_sync
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.abstraction.infrastructure.orm.models import AbstractionRuleModel
from apps.concepts.infrastructure.orm.models import ConceptCandidateModel
from apps.design_projects.infrastructure.orm.models import DesignProject
from apps.design_sessions.application.use_cases.create_session import CreateSessionUseCase
from apps.design_sessions.application.use_cases.transition_session import TransitionSessionUseCase
from apps.design_sessions.infrastructure.orm.models import DecisionLog, DesignBrief, DesignSession
from apps.design_sessions.infrastructure.repositories.brief_repository import DjangoBriefRepository
from apps.design_sessions.infrastructure.repositories.decision_log_repository import DjangoDecisionLogRepository
from apps.design_sessions.infrastructure.repositories.session_repository import DjangoSessionRepository
from apps.generation.infrastructure.orm.models import GeneratedDesignModel, GenerationJobModel
from apps.model_catalog.infrastructure.orm.models import ModelCatalogModel, ModelProviderModel
from apps.references.infrastructure.orm.models import ReferenceAsset
from apps.trend_knowledge.infrastructure.orm.models import TrendSource
from shared.presentation.base_views import BaseAPIView


def _project_dict(project: DesignProject) -> dict:
    return {
        "id": str(project.id),
        "title": project.title,
        "name": project.title,
        "description": "",
        "domain": project.domain,
        "status": project.status,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "session_count": DesignSession.objects.filter(project_id=project.id).count(),
    }


def _brief_map(session_ids) -> dict:
    briefs = DesignBrief.objects.filter(session_id__in=session_ids)
    return {str(brief.session_id): brief for brief in briefs}


def _session_dict(session: DesignSession, brief: DesignBrief | None = None) -> dict:
    title = brief.purpose if brief else ""
    description = brief.audience if brief else ""
    return {
        "id": str(session.id),
        "project_id": str(session.project_id),
        "session_title": title,
        "title": title,
        "description": description,
        "status": session.status,
        "mode": session.mode,
        "current_step": session.current_step,
        "progress_percent": round((session.current_step / 17) * 100, 2),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


class V1ProjectListCreateAPIView(BaseAPIView):
    def get(self, request):
        limit = int(request.query_params.get("limit", 100))
        projects = DesignProject.objects.filter(is_deleted=False).order_by("-created_at")[:limit]
        return Response([_project_dict(project) for project in projects])

    def post(self, request):
        title = (request.data.get("title") or request.data.get("name") or "").strip()
        if not title:
            return Response({"detail": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
        domain = request.data.get("domain") or "fashion"
        valid_domains = {choice[0] for choice in DesignProject._meta.get_field("domain").choices}
        if domain not in valid_domains:
            return Response({"detail": "invalid domain"}, status=status.HTTP_400_BAD_REQUEST)
        project = DesignProject.all_objects.create(
            id=uuid4(),
            tenant_id=request.tenant_id,
            workspace_id=request.workspace_id,
            title=title,
            domain=domain,
            status="active",
            owner_id=request.current_user_id,
        )
        return Response(_project_dict(project), status=status.HTTP_201_CREATED)


class V1ProjectDetailAPIView(BaseAPIView):
    def get(self, request, pk):
        project = self._get_project(pk)
        if project is None:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_project_dict(project))

    def patch(self, request, pk):
        project = self._get_project(pk)
        if project is None:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        title = request.data.get("title") or request.data.get("name")
        if title is not None:
            title = title.strip()
            if not title:
                return Response({"detail": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
            project.title = title
            project.save(update_fields=["title", "updated_at"])
        return Response(_project_dict(project))

    def delete(self, request, pk):
        project = self._get_project(pk)
        if project is None:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        project.status = "deleted"
        project.is_deleted = True
        project.deleted_at = timezone.now()
        project.save(update_fields=["status", "is_deleted", "deleted_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_project(self, pk):
        try:
            return DesignProject.objects.get(id=pk, is_deleted=False)
        except DesignProject.DoesNotExist:
            return None


class V1SessionListCreateAPIView(BaseAPIView):
    def get(self, request):
        sessions = DesignSession.objects.all().order_by("-created_at")
        if request.query_params.get("project_id"):
            sessions = sessions.filter(project_id=request.query_params["project_id"])
        if request.query_params.get("status"):
            sessions = sessions.filter(status=request.query_params["status"])
        limit = int(request.query_params.get("limit", 100))
        rows = list(sessions[:limit])
        briefs = _brief_map([row.id for row in rows])
        return Response([_session_dict(row, briefs.get(str(row.id))) for row in rows])

    def post(self, request):
        project_id = request.data.get("project_id")
        if not project_id:
            return Response({"detail": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            project_uuid = UUID(str(project_id))
        except ValueError:
            return Response({"detail": "invalid project_id"}, status=status.HTTP_400_BAD_REQUEST)
        session_repo = DjangoSessionRepository()
        brief_repo = DjangoBriefRepository()
        decision_repo = DjangoDecisionLogRepository()
        use_case = CreateSessionUseCase(session_repo, brief_repo, decision_repo)
        session = async_to_sync(use_case.execute)(
            project_id=project_uuid,
            started_by=request.current_user_id,
            tenant_id=request.tenant_id,
            workspace_id=request.workspace_id,
            mode=request.data.get("mode", "guided"),
            purpose=request.data.get("session_title") or request.data.get("title") or request.data.get("purpose", ""),
            audience=request.data.get("description") or request.data.get("audience", ""),
            usage_context=request.data.get("usage_context", ""),
            constraints=request.data.get("constraints", ""),
            result_form=request.data.get("result_form", "spec"),
        )
        return Response(_session_dict(session), status=status.HTTP_201_CREATED)


class V1SessionDetailAPIView(BaseAPIView):
    def get(self, request, pk):
        session = self._get_session(pk)
        if session is None:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        brief = DesignBrief.objects.filter(session_id=session.id).first()
        return Response(_session_dict(session, brief))

    def patch(self, request, pk):
        session = self._get_session(pk)
        if session is None:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        mode = request.data.get("mode")
        if mode in {"guided", "auto"}:
            session.mode = mode
            session.save(update_fields=["mode", "updated_at"])
        brief = DesignBrief.objects.filter(session_id=session.id).first()
        if brief:
            fields = []
            title = request.data.get("session_title") or request.data.get("title")
            if title is not None:
                brief.purpose = title.strip()
                fields.append("purpose")
            description = request.data.get("description")
            if description is not None:
                brief.audience = description.strip()
                fields.append("audience")
            if fields:
                fields.append("updated_at")
                brief.save(update_fields=fields)
        return Response(_session_dict(session, brief))

    def delete(self, request, pk):
        return Response(
            {"detail": "session deletion is not supported because workflow audit retention is required"},
            status=status.HTTP_409_CONFLICT,
        )

    def _get_session(self, pk):
        try:
            return DesignSession.objects.get(id=pk)
        except DesignSession.DoesNotExist:
            return None


class V1SessionRunAPIView(BaseAPIView):
    def post(self, request, pk):
        session_repo = DjangoSessionRepository()
        decision_repo = DjangoDecisionLogRepository()
        use_case = TransitionSessionUseCase(session_repo, decision_repo)
        session = async_to_sync(use_case.execute)(
            session_id=pk,
            target_state="researching",
            actor_kind="user",
            actor_id=request.current_user_id,
            rationale="run_analysis",
            evidence_refs=[],
        )
        return Response(_session_dict(session))


class V1SessionLogsAPIView(BaseAPIView):
    def get(self, request, pk):
        logs = DecisionLog.objects.filter(session_id=pk).order_by("-created_at")
        limit = int(request.query_params.get("limit", 100))
        return Response([
            {
                "id": str(log.id),
                "step": log.step,
                "action": log.action,
                "actor_kind": log.actor_kind,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs[:limit]
        ])


class V1SessionResultsAPIView(BaseAPIView):
    def get(self, request, pk):
        jobs = {job.id: job for job in GenerationJobModel.objects.filter(session_id=pk)}
        designs = GeneratedDesignModel.objects.filter(job_id__in=jobs.keys()).order_by("-created_at")
        return Response([
            {
                "id": str(design.id),
                "url": design.asset_uri,
                "kind": jobs[design.job_id].kind if design.job_id in jobs else "",
                "created_at": design.created_at.isoformat(),
            }
            for design in designs[:100]
        ])


class V1LibraryAPIView(BaseAPIView):
    def get(self, request):
        sessions = DesignSession.objects.all().values_list("id", flat=True)
        references = ReferenceAsset.objects.filter(session_id__in=sessions).order_by("-collected_at")
        return Response([
            {
                "id": str(item.id),
                "title": item.title,
                "thumbnail_url": item.thumbnail_uri,
                "url": item.source_url or item.external_url,
                "provider": item.provider,
                "created_at": item.created_at.isoformat(),
            }
            for item in references[: int(request.query_params.get("limit", 100))]
        ])


class V1IdeasAPIView(BaseAPIView):
    def get(self, request):
        sessions = DesignSession.objects.all().values_list("id", flat=True)
        ideas = ConceptCandidateModel.objects.filter(session_id__in=sessions).order_by("-created_at")
        return Response([
            {
                "id": str(item.id),
                "session_id": str(item.session_id),
                "title": item.title,
                "description": item.description,
                "status": item.status,
                "created_at": item.created_at.isoformat(),
            }
            for item in ideas[:100]
        ])


class V1CrawlersAPIView(BaseAPIView):
    def get(self, request):
        sources = TrendSource.objects.filter(active=True).order_by("name")
        return Response([
            {
                "id": str(source.id),
                "name": source.name,
                "url": source.url,
                "domain": source.domain,
                "active": source.active,
                "trust_level": source.trust_level,
            }
            for source in sources
        ])


class V1SettingsAPIView(BaseAPIView):
    def get(self, request):
        providers = ModelProviderModel.objects.order_by("name")
        return Response({
            "providers": [
                {
                    "id": provider.id,
                    "name": provider.name,
                    "active": provider.active,
                    "api_key_env": provider.api_key_env,
                    "api_key_configured": bool(os.environ.get(provider.api_key_env)),
                }
                for provider in providers
            ]
        })

    def post(self, request):
        return Response(
            {"detail": "runtime settings are managed through the model admin configuration"},
            status=status.HTTP_409_CONFLICT,
        )

    patch = post
    put = post


class V1ImageModelsAPIView(BaseAPIView):
    def get(self, request):
        models = ModelCatalogModel.objects.filter(active=True, type="image").order_by("provider__name", "model_name")
        return Response([
            {
                "id": model.id,
                "provider": model.provider.name,
                "model_name": model.model_name,
                "active": model.active,
            }
            for model in models
        ])


class V1ApiStatusAPIView(BaseAPIView):
    def get(self, request):
        providers = ModelProviderModel.objects.filter(active=True).order_by("name")
        return Response({
            provider.name: bool(os.environ.get(provider.api_key_env))
            for provider in providers
        })


class V1ReportsAPIView(BaseAPIView):
    def get(self, request):
        sessions = DesignSession.objects.all().values_list("id", flat=True)
        rules = AbstractionRuleModel.objects.filter(session_id__in=sessions).order_by("-created_at")
        return Response([
            {
                "id": str(rule.id),
                "session_id": str(rule.session_id),
                "axis": rule.axis,
                "observation": rule.observation,
                "created_at": rule.created_at.isoformat(),
            }
            for rule in rules[:100]
        ])
