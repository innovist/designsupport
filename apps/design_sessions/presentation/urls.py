"""URL configuration for design sessions presentation layer."""
from django.urls import path

from apps.design_sessions.presentation.views import (
    SessionCreateAPIView,
    SessionDecisionAPIView,
    SessionDetailAPIView,
    SessionModeAPIView,
    SessionRetryAPIView,
    SessionRerunAPIView,
    SessionTransitionAPIView,
    WorkspaceView,
)
from apps.design_sessions.presentation.workspace_api import (
    SessionAbstractionRulesAPIView,
    SessionConceptsAPIView,
    SessionEvidenceAPIView,
    SessionGenerationsAPIView,
    SessionListAPIView,
    SessionMessagesAPIView,
    SessionReferencesAPIView,
    SessionSketchAPIView,
    SessionSpecAPIView,
)

app_name = "design_sessions"

urlpatterns = [
    # Template view
    path("workspace/<uuid:session_id>/", WorkspaceView.as_view(), name="workspace"),
    path("", SessionListAPIView.as_view(), name="session-list"),
    # REST API — sessions resource
    path("<uuid:pk>/", SessionDetailAPIView.as_view(), name="session-detail"),
    path("<uuid:pk>/messages", SessionMessagesAPIView.as_view(), name="session-messages"),
    path("<uuid:pk>/sketches", SessionSketchAPIView.as_view(), name="session-sketches"),
    path("<uuid:pk>/sketches/latest", SessionSketchAPIView.as_view(), name="session-sketch-latest"),
    path("<uuid:pk>/sketches/interpretation", SessionSketchAPIView.as_view(), name="session-sketch-interpretation"),
    path("<uuid:pk>/evidence", SessionEvidenceAPIView.as_view(), name="session-evidence"),
    path("<uuid:pk>/references", SessionReferencesAPIView.as_view(), name="session-references"),
    path("<uuid:pk>/abstraction-rules", SessionAbstractionRulesAPIView.as_view(), name="session-abstraction-rules"),
    path("<uuid:pk>/generations", SessionGenerationsAPIView.as_view(), name="session-generations"),
    path("<uuid:pk>/generate", SessionGenerationsAPIView.as_view(), name="session-generate"),
    path("<uuid:pk>/concepts", SessionConceptsAPIView.as_view(), name="session-concepts"),
    path("<uuid:pk>/concepts/<uuid:concept_id>/decide", SessionConceptsAPIView.as_view(), name="session-concept-decision"),
    path("<uuid:pk>/spec", SessionSpecAPIView.as_view(), name="session-spec"),
    path("<uuid:pk>/spec/sections/<str:section_id>/memo", SessionSpecAPIView.as_view(), name="session-spec-memo"),
    path("<uuid:pk>/transitions/", SessionTransitionAPIView.as_view(), name="session-transition"),
    path("<uuid:pk>/decisions/", SessionDecisionAPIView.as_view(), name="session-decision"),
    path("<uuid:pk>/retry/", SessionRetryAPIView.as_view(), name="session-retry"),
    path("<uuid:pk>/rerun/", SessionRerunAPIView.as_view(), name="session-rerun"),
    path("<uuid:pk>/mode/", SessionModeAPIView.as_view(), name="session-mode"),
]
