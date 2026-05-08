"""Django views for admin console screens.

Implements all admin template rendering with proper authentication and authorization.
Uses application use cases through dependency injection.
"""
from datetime import datetime
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.views import View

from apps.admin_console.application.use_cases import (
    GetAdminDashboard,
    GetMetrics,
    GetPolicyDetail,
    SearchAuditLogs,
    GetJobQueue,
    EditPolicy,
    RollbackPolicy,
)
from apps.admin_console.application.ports import (
    ModelCatalogPort,
    PolicyPort,
    AuditLogPort,
    MetricsPort,
    JobQueuePort,
    PolicyChangeLogPort,
)
from apps.admin_console.infrastructure.repositories import (
    ModelCatalogRepository,
    PolicyRepository,
    AuditLogRepository,
    MetricsRepository,
    JobQueueRepository,
    PolicyChangeLogRepository,
)
from apps.admin_console.domain.entities import AdminSession, AdminRole, PolicyChangeLogEntry
from apps.admin_console.domain.value_objects import AuditLogFilter, JobQueueFilter
from shared.application.result import Result


class AdminViewMixin(LoginRequiredMixin):
    """Mixin for admin views with common functionality."""

    def get_admin_session(self) -> AdminSession:
        """Build admin session from request user."""
        # TODO: Load actual role and permissions from user profile
        return AdminSession(
            user_id=self.request.user.id,
            role=AdminRole.VIEWER,  # Default to viewer
            tenant_id=None,
        )

    def get_paginated_data(
        self, queryset: list, page: int = 1, per_page: int = 20
    ) -> dict[str, Any]:
        """Paginate queryset data."""
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        return {
            "items": page_obj.object_list,
            "pagination": {
                "page": page_obj.number,
                "pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "total": paginator.count,
            },
        }

    def handle_error(self, result: Result) -> HttpResponse:
        """Handle error result and return appropriate response."""
        return JsonResponse(
            {
                "error": result.error.message,
                "error_code": result.error.error_code,
                "details": result.error.details,
            },
            status=400 if result.error.error_code == "VALIDATION_ERROR" else 500,
        )

    def get_model_catalog_port(self) -> ModelCatalogPort:
        """Get model catalog port instance."""
        return ModelCatalogRepository()

    def get_policy_port(self) -> PolicyPort:
        """Get policy port instance."""
        return PolicyRepository()

    def get_audit_log_port(self) -> AuditLogPort:
        """Get audit log port instance."""
        return AuditLogRepository()

    def get_metrics_port(self) -> MetricsPort:
        """Get metrics port instance."""
        return MetricsRepository()

    def get_job_queue_port(self) -> JobQueuePort:
        """Get job queue port instance."""
        return JobQueueRepository()

    def get_policy_change_log_port(self) -> PolicyChangeLogPort:
        """Get policy change log port instance."""
        return PolicyChangeLogRepository()


# @MX:ANCHOR: Dashboard View - Main admin dashboard with metrics summary
# @MX:REASON: Primary entry point for admin console, aggregates data from multiple ports
class DashboardView(AdminViewMixin, TemplateView):
    """Admin dashboard with metrics summary and recent activity."""

    template_name = "admin/dashboard.html"

    # @MX:NOTE: asyncio.run() pattern for calling async repos from sync Django views
    # @MX:REASON: Django views are synchronous; domain repositories use async/await
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get dashboard context with metrics and activity."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Use GetAdminDashboard use case
        use_case = GetAdminDashboard(
            metrics_port=self.get_metrics_port(),
            policy_port=self.get_policy_port(),
            policy_log_port=self.get_policy_change_log_port(),
            job_queue_port=self.get_job_queue_port(),
        )

        # Execute use case
        import asyncio
        try:
            result = asyncio.run(use_case.execute(session))

            if result.is_success:
                dashboard_data = result.value
                context.update({
                    "skeleton": False,
                    "metrics": {
                        "total_cost": dashboard_data.metrics_summary.total_cost,
                        "total_tokens": dashboard_data.metrics_summary.total_tokens,
                        "total_invocations": dashboard_data.metrics_summary.total_invocations,
                        "successful_invocations": dashboard_data.metrics_summary.successful_invocations,
                        "failed_invocations": dashboard_data.metrics_summary.failed_invocations,
                        "failure_rate": dashboard_data.metrics_summary.failure_rate,
                    },
                    "recent_changes": [
                        {
                            "id": str(entry.id),
                            "policy_id": entry.policy_id,
                            "policy_type": entry.policy_type,
                            "version": entry.version,
                            "changed_by": str(entry.changed_by),
                            "change_type": entry.change_type,
                            "change_summary": entry.change_summary,
                            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                        }
                        for entry in dashboard_data.recent_policy_changes
                    ],
                    "active_jobs_count": dashboard_data.active_jobs_count,
                    "pending_actions_count": dashboard_data.pending_actions_count,
                    "system_health": dashboard_data.system_health,
                })
            else:
                # Return empty metrics on error
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load dashboard",
                    "metrics": {
                        "total_cost": 0.0,
                        "total_tokens": 0,
                        "total_invocations": 0,
                        "successful_invocations": 0,
                        "failed_invocations": 0,
                        "failure_rate": 0.0,
                    },
                    "recent_changes": [],
                    "active_jobs_count": 0,
                    "pending_actions_count": 0,
                    "system_health": {
                        "status": "error",
                        "last_check": datetime.now().isoformat(),
                    },
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "metrics": {
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "total_invocations": 0,
                    "successful_invocations": 0,
                    "failed_invocations": 0,
                    "failure_rate": 0.0,
                },
                "recent_changes": [],
                "active_jobs_count": 0,
                "pending_actions_count": 0,
                "system_health": {
                    "status": "error",
                    "last_check": datetime.now().isoformat(),
                },
            })

        return context


# @MX:NOTE: Repeated asyncio.run() pattern in all admin views for async port calls
# @MX:REASON: Django template views are synchronous; ports use async for I/O
class ProvidersListView(AdminViewMixin, TemplateView):
    """List all model providers with CRUD operations."""

    template_name = "admin/providers.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get providers list context."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Get page number
        page = int(self.request.GET.get("page", 1))

        # Use ModelCatalogPort to fetch providers
        import asyncio
        try:
            port = self.get_model_catalog_port()
            result = asyncio.run(port.list_providers(session))

            if result.is_success:
                providers = result.value
                paginated_data = self.get_paginated_data(providers, page)

                context.update({
                    "skeleton": False,
                    "providers": paginated_data["items"],
                    "pagination": paginated_data["pagination"],
                })
            else:
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load providers",
                    "providers": [],
                    "pagination": {
                        "page": page,
                        "pages": 1,
                        "has_next": False,
                        "has_previous": False,
                        "total": 0,
                    },
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "providers": [],
                "pagination": {
                    "page": page,
                    "pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "total": 0,
                },
            })

        return context


class ModelsListView(AdminViewMixin, TemplateView):
    """List all models with filtering and search."""

    template_name = "admin/models.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get models list context."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Get filter parameters
        provider_id = self.request.GET.get("provider")
        model_type = self.request.GET.get("type")
        page = int(self.request.GET.get("page", 1))

        # Use ModelCatalogPort to fetch models
        import asyncio
        try:
            port = self.get_model_catalog_port()
            result = asyncio.run(port.list_models(session))

            if result.is_success:
                models = result.value

                # Apply filters
                if provider_id:
                    models = [m for m in models if m.get("provider_id") == provider_id]
                if model_type:
                    models = [m for m in models if m.get("type") == model_type]

                paginated_data = self.get_paginated_data(models, page)

                context.update({
                    "skeleton": False,
                    "models": paginated_data["items"],
                    "filters": {
                        "provider": provider_id,
                        "type": model_type,
                    },
                    "pagination": paginated_data["pagination"],
                })
            else:
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load models",
                    "models": [],
                    "filters": {
                        "provider": provider_id,
                        "type": model_type,
                    },
                    "pagination": {
                        "page": page,
                        "pages": 1,
                        "has_next": False,
                        "has_previous": False,
                        "total": 0,
                    },
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "models": [],
                "filters": {
                    "provider": provider_id,
                    "type": model_type,
                },
                "pagination": {
                    "page": page,
                    "pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "total": 0,
                },
            })

        return context


class PoliciesListView(AdminViewMixin, TemplateView):
    """List all feature policies with version history."""

    template_name = "admin/policies.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get policies list context."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Get filter parameters
        feature_key = self.request.GET.get("feature")
        page = int(self.request.GET.get("page", 1))

        # Use PolicyPort to fetch policies
        import asyncio
        try:
            port = self.get_policy_port()
            result = asyncio.run(port.list_feature_policies(session))

            if result.is_success:
                policies = result.value

                # Apply filters
                if feature_key:
                    policies = [p for p in policies if p.get("feature_key") == feature_key]

                paginated_data = self.get_paginated_data(policies, page)

                context.update({
                    "skeleton": False,
                    "policies": paginated_data["items"],
                    "filters": {
                        "feature": feature_key,
                    },
                    "pagination": paginated_data["pagination"],
                })
            else:
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load policies",
                    "policies": [],
                    "filters": {
                        "feature": feature_key,
                    },
                    "pagination": {
                        "page": page,
                        "pages": 1,
                        "has_next": False,
                        "has_previous": False,
                        "total": 0,
                    },
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "policies": [],
                "filters": {
                    "feature": feature_key,
                },
                "pagination": {
                    "page": page,
                    "pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "total": 0,
                },
            })

        return context


class PromptPoliciesListView(AdminViewMixin, TemplateView):
    """List all prompt policies with version history."""

    template_name = "admin/prompt_policies.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get prompt policies list context."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Get filter parameters
        feature_key = self.request.GET.get("feature")
        page = int(self.request.GET.get("page", 1))

        # Use PolicyPort to fetch prompt policies
        import asyncio
        try:
            port = self.get_policy_port()
            result = asyncio.run(port.list_prompt_policies(session))

            if result.is_success:
                policies = result.value

                # Apply filters
                if feature_key:
                    policies = [p for p in policies if p.get("feature_key") == feature_key]

                paginated_data = self.get_paginated_data(policies, page)

                context.update({
                    "skeleton": False,
                    "prompt_policies": paginated_data["items"],
                    "filters": {
                        "feature": feature_key,
                    },
                    "pagination": paginated_data["pagination"],
                })
            else:
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load prompt policies",
                    "prompt_policies": [],
                    "filters": {
                        "feature": feature_key,
                    },
                    "pagination": {
                        "page": page,
                        "pages": 1,
                        "has_next": False,
                        "has_previous": False,
                        "total": 0,
                    },
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "prompt_policies": [],
                "filters": {
                    "feature": feature_key,
                },
                "pagination": {
                    "page": page,
                    "pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "total": 0,
                },
            })

        return context


class MetricsView(AdminViewMixin, TemplateView):
    """Display metrics with filtering by period and feature."""

    template_name = "admin/metrics.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get metrics context."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Get filter parameters
        period = self.request.GET.get("period", "daily")
        start_date = self.request.GET.get("start_date", datetime.now().strftime("%Y-%m-%d"))
        end_date = self.request.GET.get("end_date", datetime.now().strftime("%Y-%m-%d"))
        feature_key = self.request.GET.get("feature_key", None) or None

        # Use GetMetrics use case
        import asyncio
        try:
            use_case = GetMetrics(metrics_port=self.get_metrics_port())
            result = asyncio.run(use_case.execute(period, start_date, end_date, feature_key, session))

            if result.is_success:
                metrics = result.value
                context.update({
                    "skeleton": False,
                    "metrics": {
                        "period": period,
                        "start_date": start_date,
                        "end_date": end_date,
                        "feature_key": feature_key,
                        "total_cost": metrics.total_cost,
                        "cost_by_feature": metrics.cost_by_feature,
                        "total_tokens": metrics.total_tokens,
                        "tokens_by_feature": metrics.tokens_by_feature,
                        "prompt_tokens": metrics.prompt_tokens,
                        "completion_tokens": metrics.completion_tokens,
                        "total_invocations": metrics.total_invocations,
                        "invocations_by_feature": metrics.invocations_by_feature,
                        "successful_invocations": metrics.successful_invocations,
                        "failed_invocations": metrics.failed_invocations,
                        "failure_rate": metrics.failure_rate,
                        "failure_reasons": metrics.failure_reasons,
                    },
                    "filters": {
                        "period": period,
                        "start_date": start_date,
                        "end_date": end_date,
                        "feature_key": feature_key,
                    },
                })
            else:
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load metrics",
                    "metrics": {
                        "period": period,
                        "start_date": start_date,
                        "end_date": end_date,
                        "feature_key": feature_key,
                        "total_cost": 0.0,
                        "cost_by_feature": {},
                        "total_tokens": 0,
                        "tokens_by_feature": {},
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_invocations": 0,
                        "invocations_by_feature": {},
                        "successful_invocations": 0,
                        "failed_invocations": 0,
                        "failure_rate": 0.0,
                        "failure_reasons": {},
                    },
                    "filters": {
                        "period": period,
                        "start_date": start_date,
                        "end_date": end_date,
                        "feature_key": feature_key,
                    },
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "metrics": {
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "feature_key": feature_key,
                    "total_cost": 0.0,
                    "cost_by_feature": {},
                    "total_tokens": 0,
                    "tokens_by_feature": {},
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_invocations": 0,
                    "invocations_by_feature": {},
                    "successful_invocations": 0,
                    "failed_invocations": 0,
                    "failure_rate": 0.0,
                    "failure_reasons": {},
                },
                "filters": {
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "feature_key": feature_key,
                },
            })

        return context


class AuditLogsView(AdminViewMixin, TemplateView):
    """Display audit logs with filtering."""

    template_name = "admin/audit_logs.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get audit logs context."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Get filter parameters
        policy_type = self.request.GET.get("policy_type", "")
        actor = self.request.GET.get("actor", "")
        start_date = self.request.GET.get("start_date", "")
        end_date = self.request.GET.get("end_date", "")
        page = int(self.request.GET.get("page", 1))

        # Build filter object
        filters = AuditLogFilter(
            actor_id=actor or None,
            target_type=policy_type or None,
            start_date=start_date or None,
            end_date=end_date or None,
            limit=100,
            offset=(page - 1) * 100,
        )

        # Use SearchAuditLogs use case
        import asyncio
        try:
            use_case = SearchAuditLogs(audit_log_port=self.get_audit_log_port())
            result = asyncio.run(use_case.execute(filters, session))

            if result.is_success:
                logs = result.value
                context.update({
                    "skeleton": False,
                    "audit_logs": logs,
                    "filters": {
                        "policy_type": policy_type,
                        "actor": actor,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                    "pagination": {
                        "page": page,
                        "pages": 1,
                        "has_next": False,
                        "has_previous": False,
                        "total": len(logs),
                    },
                })
            else:
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load audit logs",
                    "audit_logs": [],
                    "filters": {
                        "policy_type": policy_type,
                        "actor": actor,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                    "pagination": {
                        "page": page,
                        "pages": 1,
                        "has_next": False,
                        "has_previous": False,
                        "total": 0,
                    },
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "audit_logs": [],
                "filters": {
                    "policy_type": policy_type,
                    "actor": actor,
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "pagination": {
                    "page": page,
                    "pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "total": 0,
                },
            })

        return context


class RollbackView(AdminViewMixin, TemplateView):
    """Display policy version history and rollback interface."""

    template_name = "admin/rollback.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get rollback context."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Get parameters
        policy_type = self.request.GET.get("policy_type", "feature")
        feature_key = self.request.GET.get("feature_key", "")

        # Use GetPolicyDetail use case to fetch policy history
        import asyncio
        try:
            use_case = GetPolicyDetail(
                policy_port=self.get_policy_port(),
                policy_log_port=self.get_policy_change_log_port(),
            )
            result = asyncio.run(use_case.execute(policy_type, feature_key, None, session))

            if result.is_success:
                policy_data = result.value
                context.update({
                    "skeleton": False,
                    "policy_type": policy_type,
                    "feature_key": feature_key,
                    "policy_history": policy_data.get("history", []),
                    "current_version": policy_data.get("version"),
                })
            else:
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load policy history",
                    "policy_type": policy_type,
                    "feature_key": feature_key,
                    "policy_history": [],
                    "current_version": None,
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "policy_type": policy_type,
                "feature_key": feature_key,
                "policy_history": [],
                "current_version": None,
            })

        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle rollback action."""
        session = self.get_admin_session()

        policy_type = request.POST.get("policy_type", "feature")
        feature_key = request.POST.get("feature_key", "")
        to_version = int(request.POST.get("to_version", 0))
        reason = request.POST.get("reason", "")

        if not feature_key or not to_version:
            return JsonResponse(
                {"error": "Missing required parameters: feature_key, to_version"},
                status=400,
            )

        # Use RollbackPolicy use case
        import asyncio
        try:
            use_case = RollbackPolicy(
                policy_port=self.get_policy_port(),
                policy_log_port=self.get_policy_change_log_port(),
            )
            result = asyncio.run(use_case.execute(policy_type, feature_key, to_version, reason, session))

            if result.is_success:
                return JsonResponse({
                    "success": True,
                    "message": f"Successfully rolled back {policy_type} policy '{feature_key}' to version {to_version}",
                    "data": result.value,
                })
            else:
                return JsonResponse(
                    {
                        "error": result.error.message if result.error else "Rollback failed",
                        "error_code": result.error.error_code if result.error else "ROLLBACK_ERROR",
                    },
                    status=400 if result.error and result.error.error_code == "VALIDATION_ERROR" else 500,
                )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=500,
            )


class JobQueueView(AdminViewMixin, TemplateView):
    """Display job queue with filtering and retry actions."""

    template_name = "admin/job_queue.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get job queue context."""
        context = super().get_context_data(**kwargs)
        session = self.get_admin_session()

        # Get filter parameters
        status = self.request.GET.get("status", "")
        tenant_id = self.request.GET.get("tenant_id", "")
        page = int(self.request.GET.get("page", 1))

        # Build filter object
        filters = JobQueueFilter(
            status=status or None,  # type: ignore
            tenant_id=tenant_id or None,
            limit=100,
            offset=(page - 1) * 100,
        )

        # Use GetJobQueue use case
        import asyncio
        try:
            use_case = GetJobQueue(job_queue_port=self.get_job_queue_port())
            result = asyncio.run(use_case.execute(filters, session))

            if result.is_success:
                jobs = result.value
                context.update({
                    "skeleton": False,
                    "jobs": jobs,
                    "filters": {
                        "status": status,
                        "tenant_id": tenant_id,
                    },
                    "pagination": {
                        "page": page,
                        "pages": 1,
                        "has_next": False,
                        "has_previous": False,
                        "total": len(jobs),
                    },
                })
            else:
                context.update({
                    "skeleton": False,
                    "error": result.error.message if result.error else "Failed to load job queue",
                    "jobs": [],
                    "filters": {
                        "status": status,
                        "tenant_id": tenant_id,
                    },
                    "pagination": {
                        "page": page,
                        "pages": 1,
                        "has_next": False,
                        "has_previous": False,
                        "total": 0,
                    },
                })
        except Exception as e:
            context.update({
                "skeleton": False,
                "error": str(e),
                "jobs": [],
                "filters": {
                    "status": status,
                    "tenant_id": tenant_id,
                },
                "pagination": {
                    "page": page,
                    "pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "total": 0,
                },
            })

        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle job retry action."""
        session = self.get_admin_session()

        action = request.POST.get("action", "")
        job_id = request.POST.get("job_id", "")

        if action == "retry" and job_id:
            # Import UUID to validate job_id
            from uuid import UUID

            try:
                job_uuid = UUID(job_id)
            except ValueError:
                return JsonResponse(
                    {"error": "Invalid job ID format"},
                    status=400,
                )

            # Use JobQueuePort to retry job
            import asyncio
            try:
                port = self.get_job_queue_port()
                result = asyncio.run(port.retry_job(job_uuid, session))

                if result.is_success:
                    return JsonResponse({
                        "success": True,
                        "message": f"Successfully retried job {job_id}",
                        "data": result.value,
                    })
                else:
                    return JsonResponse(
                        {
                            "error": result.error.message if result.error else "Job retry failed",
                            "error_code": result.error.error_code if result.error else "RETRY_ERROR",
                        },
                        status=500,
                    )
            except Exception as e:
                return JsonResponse(
                    {"error": str(e)},
                    status=500,
                )

        return JsonResponse(
            {"error": "Invalid action"},
            status=400,
        )


# API Views for AJAX operations

class ProviderCreateView(AdminViewMixin, View):
    """Create new provider via AJAX."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle provider creation."""
        session = self.get_admin_session()

        # Get data from request
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON in request body"},
                status=400,
            )

        # Validate required fields
        required_fields = ["name", "api_key_env"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return JsonResponse(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=400,
            )

        # Use ModelCatalogPort to create provider
        import asyncio
        try:
            port = self.get_model_catalog_port()
            result = asyncio.run(port.create_provider(data, session))

            if result.is_success:
                return JsonResponse({
                    "success": True,
                    "message": "Provider created successfully",
                    "data": result.value,
                })
            else:
                return JsonResponse(
                    {
                        "error": result.error.message if result.error else "Provider creation failed",
                        "error_code": result.error.error_code if result.error else "CREATION_ERROR",
                    },
                    status=400 if result.error and result.error.error_code == "VALIDATION_ERROR" else 500,
                )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=500,
            )


class ProviderUpdateView(AdminViewMixin, View):
    """Update provider via AJAX."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle provider update."""
        session = self.get_admin_session()

        provider_id = kwargs.get("provider_id")

        if not provider_id:
            return JsonResponse(
                {"error": "Missing provider_id"},
                status=400,
            )

        # Get data from request
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON in request body"},
                status=400,
            )

        # Use ModelCatalogPort to update provider
        import asyncio
        try:
            port = self.get_model_catalog_port()
            result = asyncio.run(port.update_provider(provider_id, data, session))

            if result.is_success:
                return JsonResponse({
                    "success": True,
                    "message": "Provider updated successfully",
                    "data": result.value,
                })
            else:
                return JsonResponse(
                    {
                        "error": result.error.message if result.error else "Provider update failed",
                        "error_code": result.error.error_code if result.error else "UPDATE_ERROR",
                    },
                    status=404 if result.error and "not found" in str(result.error.message).lower() else 500,
                )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=500,
            )


class ProviderDeleteView(AdminViewMixin, View):
    """Delete/deactivate provider via AJAX."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle provider deactivation."""
        session = self.get_admin_session()

        provider_id = kwargs.get("provider_id")

        if not provider_id:
            return JsonResponse(
                {"error": "Missing provider_id"},
                status=400,
            )

        # Use ModelCatalogPort to deactivate provider
        import asyncio
        try:
            port = self.get_model_catalog_port()
            result = asyncio.run(port.deactivate_provider(provider_id, session))

            if result.is_success:
                return JsonResponse({
                    "success": True,
                    "message": "Provider deactivated successfully",
                })
            else:
                return JsonResponse(
                    {
                        "error": result.error.message if result.error else "Provider deactivation failed",
                        "error_code": result.error.error_code if result.error else "DEACTIVATION_ERROR",
                    },
                    status=404 if result.error and "not found" in str(result.error.message).lower() else 500,
                )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=500,
            )


class PolicyEditView(AdminViewMixin, View):
    """Edit feature policy via AJAX."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle policy update."""
        session = self.get_admin_session()

        feature_key = kwargs.get("feature_key")

        if not feature_key:
            return JsonResponse(
                {"error": "Missing feature_key"},
                status=400,
            )

        # Get data from request
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # Try POST data if JSON parsing fails
            data = request.POST.dict()

        # Use EditPolicy use case
        import asyncio
        try:
            use_case = EditPolicy(
                policy_port=self.get_policy_port(),
                policy_log_port=self.get_policy_change_log_port(),
            )
            result = asyncio.run(use_case.execute("feature", feature_key, data, session))

            if result.is_success:
                return JsonResponse({
                    "success": True,
                    "message": "Feature policy updated successfully",
                    "data": result.value,
                })
            else:
                return JsonResponse(
                    {
                        "error": result.error.message if result.error else "Policy update failed",
                        "error_code": result.error.error_code if result.error else "UPDATE_ERROR",
                    },
                    status=400 if result.error and result.error.error_code == "VALIDATION_ERROR" else 500,
                )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=500,
            )


class PromptPolicyEditView(AdminViewMixin, View):
    """Edit prompt policy via AJAX."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle prompt policy update."""
        session = self.get_admin_session()

        feature_key = kwargs.get("feature_key")

        if not feature_key:
            return JsonResponse(
                {"error": "Missing feature_key"},
                status=400,
            )

        # Get data from request
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # Try POST data if JSON parsing fails
            data = request.POST.dict()

        # Use EditPolicy use case
        import asyncio
        try:
            use_case = EditPolicy(
                policy_port=self.get_policy_port(),
                policy_log_port=self.get_policy_change_log_port(),
            )
            result = asyncio.run(use_case.execute("prompt", feature_key, data, session))

            if result.is_success:
                return JsonResponse({
                    "success": True,
                    "message": "Prompt policy updated successfully",
                    "data": result.value,
                })
            else:
                return JsonResponse(
                    {
                        "error": result.error.message if result.error else "Prompt policy update failed",
                        "error_code": result.error.error_code if result.error else "UPDATE_ERROR",
                    },
                    status=400 if result.error and result.error.error_code == "VALIDATION_ERROR" else 500,
                )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)},
                status=500,
            )
