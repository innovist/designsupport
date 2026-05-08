"""Runtime smoke tests for the Django user-facing workflow."""
import os

import django
from django.core.management import call_command
from django.test import Client


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
django.setup()


def _client() -> Client:
    call_command("migrate", verbosity=0, interactive=False)
    return Client()


def test_public_pages_render():
    client = _client()
    paths = [
        "/",
        "/workspace",
        "/dashboard",
        "/projects",
        "/projects/new",
        "/sessions/new",
        "/history",
        "/ideas",
        "/library",
        "/settings",
        "/chatbot",
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path


def test_signup_project_session_message_flow():
    client = _client()
    register = client.post(
        "/api/auth/register/",
        {
            "email": "flow@example.com",
            "password": "Testpass123",
            "display_name": "Flow User",
        },
        content_type="application/json",
    )
    assert register.status_code == 201
    assert register.json()["user"]["default_workspace_id"]

    workspaces = client.get("/api/workspaces/")
    assert workspaces.status_code == 200
    assert len(workspaces.json()) == 1

    project = client.post(
        "/api/projects/",
        {"title": "Runtime Project", "domain": "fashion"},
        content_type="application/json",
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    session = client.post(
        f"/api/design-projects/{project_id}/sessions/",
        {
            "mode": "guided",
            "purpose": "Backpack concept",
            "audience": "Students",
            "result_form": "image",
        },
        content_type="application/json",
    )
    assert session.status_code == 201
    session_id = session.json()["id"]

    detail = client.get(f"/api/sessions/{session_id}/")
    assert detail.status_code == 200
    assert detail.json()["brief"]["purpose"] == "Backpack concept"

    message = client.post(
        f"/api/sessions/{session_id}/messages",
        {"content": "Keep the silhouette compact."},
        content_type="application/json",
    )
    assert message.status_code == 201
    assert message.json()["role"] == "user"

    messages = client.get(f"/api/sessions/{session_id}/messages")
    assert messages.status_code == 200
    assert len(messages.json()) == 1
