"""Design project API views."""
from uuid import uuid4

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.design_projects.infrastructure.orm.models import DesignProject
from shared.presentation.base_views import BaseAPIView


def _serialize_project(project: DesignProject) -> dict:
    return {
        "id": str(project.id),
        "workspace_id": str(project.workspace_id),
        "title": project.title,
        "domain": project.domain,
        "status": project.status,
        "owner_id": str(project.owner_id),
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


class ProjectListCreateAPIView(BaseAPIView):
    """List and create projects in the current workspace."""

    def get(self, request):
        projects = DesignProject.objects.filter(
            status__in=["active", "archived"],
            is_deleted=False,
        ).order_by("-created_at")
        return Response([_serialize_project(project) for project in projects])

    def post(self, request):
        title = (request.data.get("title") or "").strip()
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
        return Response(_serialize_project(project), status=status.HTTP_201_CREATED)


class ProjectDetailAPIView(BaseAPIView):
    """Read and update a project in the current workspace."""

    def get(self, request, pk):
        try:
            project = DesignProject.objects.get(id=pk, is_deleted=False)
        except DesignProject.DoesNotExist:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_project(project))

    def patch(self, request, pk):
        try:
            project = DesignProject.objects.get(id=pk, is_deleted=False)
        except DesignProject.DoesNotExist:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)

        fields = []
        title = request.data.get("title")
        if title is not None:
            title = title.strip()
            if not title:
                return Response({"detail": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
            project.title = title
            fields.append("title")

        domain = request.data.get("domain")
        if domain is not None:
            valid_domains = {choice[0] for choice in DesignProject._meta.get_field("domain").choices}
            if domain not in valid_domains:
                return Response({"detail": "invalid domain"}, status=status.HTTP_400_BAD_REQUEST)
            project.domain = domain
            fields.append("domain")

        status_value = request.data.get("status")
        if status_value is not None:
            valid_statuses = {choice[0] for choice in DesignProject._meta.get_field("status").choices}
            if status_value not in valid_statuses:
                return Response({"detail": "invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            project.status = status_value
            fields.append("status")

        if fields:
            fields.append("updated_at")
            project.save(update_fields=fields)
        return Response(_serialize_project(project))

    def delete(self, request, pk):
        try:
            project = DesignProject.objects.get(id=pk, is_deleted=False)
        except DesignProject.DoesNotExist:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)

        project.status = "deleted"
        project.is_deleted = True
        project.deleted_at = timezone.now()
        project.save(update_fields=["status", "is_deleted", "deleted_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
