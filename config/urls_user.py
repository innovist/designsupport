"""User workspace URL configuration for port 14000."""
from django.shortcuts import render
from django.urls import include, path
from django.views.generic import TemplateView

from config.api_v1_views import (
    V1ApiStatusAPIView,
    V1CrawlersAPIView,
    V1IdeasAPIView,
    V1ImageModelsAPIView,
    V1LibraryAPIView,
    V1ProjectDetailAPIView,
    V1ProjectListCreateAPIView,
    V1ReportsAPIView,
    V1SessionDetailAPIView,
    V1SessionListCreateAPIView,
    V1SessionLogsAPIView,
    V1SessionResultsAPIView,
    V1SessionRunAPIView,
    V1SettingsAPIView,
)


WORKSPACE_STEPS = [
    {"key": str(index), "label": label}
    for index, label in enumerate(
        [
            "Purpose",
            "Brief",
            "Sketch",
            "Clarify",
            "Evidence",
            "Concepts",
            "Evaluate",
            "Decide",
            "Search",
            "Analyze",
            "Synthesize",
            "Abstract",
            "Refine",
            "Apply",
            "Compare",
            "Spec",
            "Approve",
        ],
        start=1,
    )
]

WORKSPACE_CONTEXT = {
    "current_step": "1",
    "session_id": "",
    "common": {"toggle": "Toggle panel"},
    "workspace": {
        "pageTitle": "Design Workspace",
        "projectNavigator": "Project Navigator",
        "stepBar": {"title": "Pipeline steps", "steps": WORKSPACE_STEPS},
        "navigator": {
            "projectList": "Project List",
            "sessionList": "Session List",
            "pipelineSteps": "Pipeline Steps",
        },
        "boards": {
            "title": "Design boards",
            "chat": {"title": "Chat", "placeholder": "Describe the design goal", "inputLabel": "Chat message", "sendButton": "Send"},
            "evidence": {"title": "Evidence", "filterBySource": "Filter by source", "allSources": "All Sources", "sortBy": "Sort by", "credibility": "Credibility", "recency": "Recency"},
            "sketch": {
                "title": "Sketch Input",
                "original": "Original",
                "upload": "Upload sketch",
                "interpretation": "AI Interpretation",
                "refinement": "Refinement Actions",
                "actions": {
                    "keep": "Keep",
                    "clarify": "Clarify",
                    "vary": "Vary",
                    "refine": "Refine",
                    "expand": "Expand",
                    "useAsEvidence": "Use as Evidence",
                    "runSearch": "Run Search",
                    "generate": "Generate",
                },
            },
            "reference": {"title": "Reference Search", "clusters": "Source Clusters", "grid": "Reference Grid", "analysis": "Analysis"},
            "abstraction": {"title": "Abstraction Rules"},
            "generation": {"title": "Generation Results", "comparison": "Comparison"},
            "decision": {"title": "Decision", "log": "Decision Log", "scores": {"creativity": "Creativity", "feasibility": "Feasibility", "marketFit": "Market Fit"}},
        },
        "decisionPanel": {
            "title": "Decision Panel",
            "currentStep": "Current Step",
            "briefScore": "Brief Score",
            "conceptScores": "Concept Scores",
            "selectedSketch": "Selected Sketch",
            "selectedReferences": "Selected References",
            "nextAction": "Next Action",
            "proceed": "Proceed",
            "progress": "Progress",
            "notifications": "Notifications",
        },
    },
}


def workspace_view(request):
    context = {
        **WORKSPACE_CONTEXT,
        "session_id": request.GET.get("session") or request.GET.get("session_id") or "",
    }
    return render(request, "pages/workspace.html", context)


urlpatterns = [
    # Home
    path('', TemplateView.as_view(template_name='pages/home.html'), name='home'),
    path('dashboard', TemplateView.as_view(template_name='pages/dashboard.html'), name='dashboard'),
    path('projects', TemplateView.as_view(template_name='pages/projects.html'), name='projects'),
    path('projects/new', TemplateView.as_view(template_name='pages/new_project.html'), name='new_project'),
    path(
        'projects/<path:project_id>/new-session',
        TemplateView.as_view(
            template_name='pages/new_session.html',
            extra_context={"crawler_categories": {}},
        ),
        name='new_project_session',
    ),
    path('projects/<path:project_id>', TemplateView.as_view(template_name='pages/project_detail.html'), name='project_detail'),
    path(
        'sessions/new',
        TemplateView.as_view(
            template_name='pages/new_session.html',
            extra_context={"project_id": "", "crawler_categories": {}},
        ),
        name='new_session',
    ),
    path('sessions/<path:session_id>', TemplateView.as_view(template_name='pages/session_detail.html'), name='session_detail'),
    path('history', TemplateView.as_view(template_name='pages/history.html'), name='history'),
    path('ideas', TemplateView.as_view(template_name='pages/ideas.html'), name='ideas'),
    path('library', TemplateView.as_view(template_name='pages/library.html'), name='library'),
    path('settings', TemplateView.as_view(template_name='pages/settings.html'), name='settings'),
    path('chatbot', TemplateView.as_view(template_name='pages/chatbot.html'), name='chatbot'),
    path('workspace', workspace_view, name='workspace'),

    # API endpoints
    path('api/auth/', include('apps.accounts.presentation.urls')),
    path('api/v1/projects/', V1ProjectListCreateAPIView.as_view(), name='v1-projects'),
    path('api/v1/projects/<uuid:pk>', V1ProjectDetailAPIView.as_view(), name='v1-project-detail'),
    path('api/v1/projects/<uuid:pk>/', V1ProjectDetailAPIView.as_view(), name='v1-project-detail-slash'),
    path('api/v1/sessions/', V1SessionListCreateAPIView.as_view(), name='v1-sessions'),
    path('api/v1/sessions/<uuid:pk>', V1SessionDetailAPIView.as_view(), name='v1-session-detail'),
    path('api/v1/sessions/<uuid:pk>/', V1SessionDetailAPIView.as_view(), name='v1-session-detail-slash'),
    path('api/v1/sessions/<uuid:pk>/run-analysis', V1SessionRunAPIView.as_view(), name='v1-session-run'),
    path('api/v1/sessions/<uuid:pk>/results', V1SessionResultsAPIView.as_view(), name='v1-session-results'),
    path('api/v1/sessions/<uuid:pk>/logs', V1SessionLogsAPIView.as_view(), name='v1-session-logs'),
    path('api/v1/library', V1LibraryAPIView.as_view(), name='v1-library'),
    path('api/v1/ideas/', V1IdeasAPIView.as_view(), name='v1-ideas'),
    path('api/v1/reports', V1ReportsAPIView.as_view(), name='v1-reports'),
    path('api/v1/crawlers/list', V1CrawlersAPIView.as_view(), name='v1-crawlers'),
    path('api/v1/settings/', V1SettingsAPIView.as_view(), name='v1-settings'),
    path('api/v1/settings/api-status', V1ApiStatusAPIView.as_view(), name='v1-api-status'),
    path('api/v1/settings/image-models', V1ImageModelsAPIView.as_view(), name='v1-image-models'),
    path('api/workspaces/', include('apps.workspaces.presentation.urls')),
    path('api/projects/', include('apps.design_projects.presentation.urls')),
    path('api/sessions/', include('apps.design_sessions.presentation.urls')),
    # Session creation scoped to project (Gap 2)
    path('api/design-projects/<uuid:project_id>/sessions/', include('apps.design_sessions.presentation.project_session_urls')),
    path('api/conversations/', include('apps.conversations.presentation.urls')),
    path('api/assets/', include('apps.user_assets.presentation.urls')),
    path('api/trends/', include('apps.trend_knowledge.presentation.urls')),
    path('api/references/', include('apps.references.presentation.urls')),
    path('api/concepts/', include('apps.concepts.presentation.urls')),
    path('api/abstraction/', include('apps.abstraction.presentation.urls')),
    path('api/generation/', include('apps.generation.presentation.urls')),
    path('api/specs/', include('apps.specs.presentation.urls')),
]
