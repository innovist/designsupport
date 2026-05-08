"""Django views for design sessions workspace.

Implements workspace template rendering with session data and project info.
Also provides DRF REST API views for Gap 2 (REQ-01-SESSION, REQ-01-ORCH).
"""
from uuid import UUID

from asgiref.sync import async_to_sync
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest
from django.views.generic import TemplateView
from rest_framework.response import Response

from apps.design_sessions.application.ports import (
    DesignSessionPort,
    ProjectPort,
)
from shared.presentation.base_views import BaseAPIView
from shared.presentation.error_handlers import error_handler
from apps.design_sessions.domain.entities import DesignSession, PipelineStep
from apps.design_sessions.infrastructure.repositories.brief_repository import DjangoBriefRepository
from apps.design_sessions.infrastructure.repositories.decision_log_repository import DjangoDecisionLogRepository
from apps.design_sessions.infrastructure.repositories.session_repository import DjangoSessionRepository
from shared.domain.exceptions import NotFoundError, PermissionDeniedError

# API serializers with SPEC-05-API-001 meta fields are available in serializers.py
# from apps.design_sessions.presentation.serializers import DesignSessionSerializer


class SessionViewModel:
    """View model for design session workspace.

    Provides formatted data for template rendering.
    """

    def __init__(self, session: DesignSession, project: dict | None):
        """Initialize view model.

        Args:
            session: Design session entity
            project: Project data dictionary
        """
        self.session = session
        self.project = project or {}
        self.step_mapping = self._build_step_mapping()

    def _build_step_mapping(self) -> dict[PipelineStep, dict]:
        """Build step mapping with labels and descriptions.

        Returns:
            Dictionary mapping PipelineStep to metadata
        """
        return {
            PipelineStep.PURPOSE_INPUT: {
                "label": "Purpose Input",
                "description": "Define design purpose and goals",
                "icon": "target",
            },
            PipelineStep.BRIEF_STRUCTURE: {
                "label": "Brief Structure",
                "description": "Create structured design brief",
                "icon": "file-text",
            },
            PipelineStep.SKETCH_UPLOAD: {
                "label": "Sketch Upload",
                "description": "Upload reference sketches",
                "icon": "upload",
            },
            PipelineStep.CLARIFYING_QUESTIONS: {
                "label": "Clarifying Questions",
                "description": "Answer questions for clarity",
                "icon": "help-circle",
            },
            PipelineStep.TREND_RESEARCH: {
                "label": "Trend Research",
                "description": "Research fashion trends",
                "icon": "search",
            },
            PipelineStep.CONCEPT_GENERATION: {
                "label": "Concept Generation",
                "description": "Generate design concepts",
                "icon": "lightbulb",
            },
            PipelineStep.CONCEPT_EVALUATION: {
                "label": "Concept Evaluation",
                "description": "Evaluate generated concepts",
                "icon": "check-circle",
            },
            PipelineStep.CONCEPT_DECISION: {
                "label": "Concept Decision",
                "description": "Select final concept",
                "icon": "decision",
            },
            PipelineStep.REFERENCE_SEARCH: {
                "label": "Reference Search",
                "description": "Search design references",
                "icon": "image",
            },
            PipelineStep.REFERENCE_CLUSTERING: {
                "label": "Reference Clustering",
                "description": "Cluster similar references",
                "icon": "layers",
            },
            PipelineStep.SKETCH_ANALYSIS: {
                "label": "Sketch Analysis",
                "description": "Analyze uploaded sketches",
                "icon": "edit",
            },
            PipelineStep.ABSTRACTION: {
                "label": "Abstraction",
                "description": "Extract abstract patterns",
                "icon": "grid",
            },
            PipelineStep.GENERATION: {
                "label": "Generation",
                "description": "Generate final designs",
                "icon": "sparkles",
            },
            PipelineStep.DOMAIN_APPLICATION: {
                "label": "Domain Application",
                "description": "Apply to fashion domain",
                "icon": "tshirt",
            },
            PipelineStep.COMPARISON: {
                "label": "Comparison",
                "description": "Compare with trends",
                "icon": "bar-chart",
            },
            PipelineStep.SPEC_DOCUMENT: {
                "label": "Spec Document",
                "description": "Create specification",
                "icon": "file",
            },
            PipelineStep.REVIEW: {
                "label": "Review",
                "description": "Final review and approval",
                "icon": "eye",
            },
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for template context.

        Returns:
            Dictionary with all template data
        """
        current_step_info = self.step_mapping.get(
            self.session.current_step,
            {"label": "Unknown", "description": "", "icon": "help-circle"},
        )

        return {
            "session": {
                "id": str(self.session.id),
                "project_id": str(self.session.project_id),
                "mode": self.session.mode.value,
                "status": self.session.status.value,
                "current_step": self.session.current_step.value,
                "current_step_label": current_step_info["label"],
                "current_step_description": current_step_info["description"],
                "current_step_icon": current_step_info["icon"],
                "version": self.session.version,
                "created_at": self.session.created_at.isoformat(),
                "updated_at": self.session.updated_at.isoformat(),
                "progress_percentage": self._calculate_progress(),
            },
            "project": {
                "id": str(self.project.get("id", "")),
                "name": self.project.get("name", "Unknown Project"),
                "description": self.project.get("description", ""),
            },
            "steps": [
                {
                    "number": step.value,
                    "label": info["label"],
                    "description": info["description"],
                    "icon": info["icon"],
                    "is_completed": step.value < self.session.current_step.value,
                    "is_current": step == self.session.current_step,
                    "is_pending": step.value > self.session.current_step.value,
                }
                for step, info in self.step_mapping.items()
            ],
        }

    def _calculate_progress(self) -> int:
        """Calculate session progress percentage.

        Returns:
            Progress percentage (0-100)
        """
        total_steps = len(PipelineStep)
        current_step_value = self.session.current_step.value
        return int((current_step_value / total_steps) * 100)


class WorkspaceView(LoginRequiredMixin, TemplateView):
    """Workspace view for design session management.

    Renders the workspace template with session data and project info.
    """

    template_name = "pages/workspace.html"

    def __init__(self, *args, **kwargs):
        """Initialize view with required ports."""
        super().__init__(*args, **kwargs)
        # Ports will be injected via dependency injection in real implementation
        self.session_port: DesignSessionPort | None = None
        self.project_port: ProjectPort | None = None

    def get_context_data(self, **kwargs):
        """Build template context with session data.

        Args:
            **kwargs: Route keyword arguments including session_id

        Returns:
            Template context dictionary

        Raises:
            Http404: If session not found
        """
        context = super().get_context_data(**kwargs)
        session_id = kwargs.get("session_id")

        if not session_id:
            raise Http404("Session ID is required")

        try:
            # Ports will be injected via DI when infrastructure is ready.
            # Until then, render skeleton state so the template works.
            if self.session_port is None or self.project_port is None:
                context.update({"skeleton": True, "session_id": session_id})
                return context

            session_result = async_to_sync(self.session_port.get_session)(session_id)
            if session_result.is_failure:
                raise Http404(f"Session not found: {session_id}")

            session = session_result.value
            project_result = async_to_sync(self.project_port.get_project)(
                str(session.project_id)
            )
            project = project_result.value if project_result.is_success else None

            view_model = SessionViewModel(session, project)
            context.update({"workspace": view_model.to_dict(), "skeleton": False})
            return context

        except (NotFoundError, PermissionDeniedError):
            raise Http404(f"Session not found: {session_id}")


# ---------------------------------------------------------------------------
# REST API views (Gap 2)
# ---------------------------------------------------------------------------

def _repos():
    return (
        DjangoSessionRepository(),
        DjangoBriefRepository(),
        DjangoDecisionLogRepository(),
    )


# @MX:ANCHOR: [AUTO] Session creation endpoint - starts design workflow
# @MX:REASON: High fan_in - called by workspace UI, mobile apps, API clients
class SessionCreateAPIView(BaseAPIView):
    """POST /api/design-projects/<uuid:project_id>/sessions/"""

    def post(self, request: HttpRequest, project_id: UUID) -> Response:
        from apps.design_sessions.application.use_cases.create_session import CreateSessionUseCase

        data = request.data
        session_repo, brief_repo, decision_repo = _repos()
        uc = CreateSessionUseCase(session_repo, brief_repo, decision_repo)

        try:
            session = async_to_sync(uc.execute)(
                project_id=project_id,
                started_by=request.current_user_id,  # type: ignore[attr-defined]
                tenant_id=request.tenant_id,  # type: ignore[attr-defined]
                workspace_id=request.workspace_id,  # type: ignore[attr-defined]
                mode=data.get("mode", "guided"),
                purpose=data.get("purpose", ""),
                audience=data.get("audience", ""),
                usage_context=data.get("usage_context", ""),
                constraints=data.get("constraints", ""),
                result_form=data.get("result_form", ""),
            )
            brief = getattr(session, "brief", None)
            return Response(
                {
                    "id": str(session.id),
                    "status": session.status.value,
                    "mode": session.mode.value,
                    "current_step": session.current_step.value,
                    "version": session.version,
                    "clarifying_questions": brief.clarifying_questions if brief else [],
                },
                status=201,
            )
        except Exception as exc:
            return error_handler(exc)


class SessionDetailAPIView(BaseAPIView):
    """GET /api/design-sessions/<uuid:pk>/"""

    def get(self, request: HttpRequest, pk: UUID) -> Response:
        from apps.design_sessions.application.use_cases.get_session_detail import GetSessionDetailUseCase

        session_repo, brief_repo, decision_repo = _repos()
        uc = GetSessionDetailUseCase(session_repo, brief_repo, decision_repo)

        try:
            detail = async_to_sync(uc.execute)(pk)
            s = detail.session
            b = detail.brief
            return Response(
                {
                    "id": str(s.id),
                    "project_id": str(s.project_id),
                    "status": s.status.value,
                    "mode": s.mode.value,
                    "current_step": s.current_step.value,
                    "version": s.version,
                    "brief": {
                        "purpose": b.purpose,
                        "audience": b.audience,
                        "result_form": b.result_form,
                        "clarifying_questions": b.clarifying_questions,
                    } if b else None,
                    "decisions": [
                        {
                            "id": str(d.id),
                            "step": d.step.value,
                            "action": d.action,
                            "actor_kind": d.actor_kind,
                        }
                        for d in detail.decisions
                    ],
                }
            )
        except Exception as exc:
            return error_handler(exc)


# @MX:ANCHOR: [AUTO] State transition endpoint - workflow progression
# @MX:REASON: High fan_in - called by orchestrator, manual step triggers, retry flows
class SessionTransitionAPIView(BaseAPIView):
    """POST /api/design-sessions/<uuid:pk>/transitions/"""

    def post(self, request: HttpRequest, pk: UUID) -> Response:
        from apps.design_sessions.application.use_cases.transition_session import TransitionSessionUseCase

        session_repo, _b, decision_repo = _repos()
        uc = TransitionSessionUseCase(session_repo, decision_repo)

        data = request.data
        try:
            session = async_to_sync(uc.execute)(
                session_id=pk,
                target_state=data.get("target_state", ""),
                actor_kind=data.get("actor_kind", "user"),
                actor_id=request.current_user_id,  # type: ignore[attr-defined]
                rationale=data.get("rationale", ""),
                evidence_refs=data.get("evidence_refs"),
            )
            return Response({"id": str(session.id), "status": session.status.value})
        except Exception as exc:
            return error_handler(exc)


class SessionDecisionAPIView(BaseAPIView):
    """POST /api/design-sessions/<uuid:pk>/decisions/"""

    def post(self, request: HttpRequest, pk: UUID) -> Response:
        from apps.design_sessions.application.use_cases.record_decision import RecordDecisionUseCase

        _s, _b, decision_repo = _repos()
        uc = RecordDecisionUseCase(decision_repo)

        data = request.data
        try:
            decision = async_to_sync(uc.execute)(
                session_id=pk,
                step=int(data.get("step", 1)),
                action=data.get("action", ""),
                actor_kind=data.get("actor_kind", "user"),
                actor_id=request.current_user_id,  # type: ignore[attr-defined]
                rationale=data.get("rationale", ""),
                evidence_refs=data.get("evidence_refs"),
            )
            return Response({"id": str(decision.id), "step": decision.step.value}, status=201)
        except Exception as exc:
            return error_handler(exc)


# @MX:WARN: [AUTO] Retry endpoint mutates session state - requires validation
# @MX:REASON: State mutation with side effects, failure tracking, version increment
class SessionRetryAPIView(BaseAPIView):
    """POST /api/design-sessions/<uuid:pk>/retry/"""

    def post(self, request: HttpRequest, pk: UUID) -> Response:
        from apps.design_sessions.application.use_cases.retry_step import RetryStepUseCase

        session_repo, _b, decision_repo = _repos()
        uc = RetryStepUseCase(session_repo, decision_repo)

        try:
            session = async_to_sync(uc.execute)(
                session_id=pk,
                actor_id=request.current_user_id,  # type: ignore[attr-defined]
            )
            return Response({"id": str(session.id), "status": session.status.value})
        except Exception as exc:
            return error_handler(exc)


class SessionRerunAPIView(BaseAPIView):
    """POST /api/design-sessions/<uuid:pk>/rerun/"""

    def post(self, request: HttpRequest, pk: UUID) -> Response:
        from apps.design_sessions.application.use_cases.rerun_from_step import RerunFromStepUseCase

        session_repo, _b, decision_repo = _repos()
        uc = RerunFromStepUseCase(session_repo, decision_repo)

        data = request.data
        try:
            session = async_to_sync(uc.execute)(
                session_id=pk,
                from_step=int(data.get("from_step", 1)),
                actor_id=request.current_user_id,  # type: ignore[attr-defined]
                rationale=data.get("rationale", ""),
            )
            return Response(
                {
                    "id": str(session.id),
                    "status": session.status.value,
                    "current_step": session.current_step.value,
                    "version": session.version,
                }
            )
        except Exception as exc:
            return error_handler(exc)


class SessionModeAPIView(BaseAPIView):
    """POST /api/design-sessions/<uuid:pk>/mode/"""

    def post(self, request: HttpRequest, pk: UUID) -> Response:
        from apps.design_sessions.application.use_cases.switch_mode import SwitchModeUseCase

        session_repo, _b, decision_repo = _repos()
        uc = SwitchModeUseCase(session_repo, decision_repo)

        data = request.data
        try:
            session = async_to_sync(uc.execute)(
                session_id=pk,
                new_mode=data.get("mode", "guided"),
                actor_id=request.current_user_id,  # type: ignore[attr-defined]
                rationale=data.get("rationale", ""),
            )
            return Response({"id": str(session.id), "mode": session.mode.value})
        except Exception as exc:
            return error_handler(exc)
