"""
Integration tests using FastAPI TestClient (no external API calls)
"""

from fastapi.testclient import TestClient

from main import app
from app.crawler_config import get_all_crawlers


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"


def test_settings_login_and_status():
    login = client.post("/api/v1/settings/login")
    assert login.status_code == 200
    token = login.json().get("token")
    assert token

    status = client.get(
        "/api/v1/settings/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status.status_code == 200
    payload = status.json()
    assert "status" in payload


def test_crawler_sources():
    response = client.get("/api/v1/crawler/sources")
    assert response.status_code == 200
    payload = response.json()
    sources = payload["data"]["sources"]
    assert len(sources) == len(get_all_crawlers())


def test_blueprint_metadata_endpoints():
    size_systems = client.get("/api/v1/blueprint/size-systems")
    assert size_systems.status_code == 200
    assert "size_systems" in size_systems.json()

    garment_types = client.get("/api/v1/blueprint/garment-types")
    assert garment_types.status_code == 200
    assert "garment_types" in garment_types.json()


def test_projects_and_sessions_flow():
    project_payload = {
        "title": "Test Project",
        "description": "Integration test project",
        "prompt": "Spring casual fashion",
        "language": "ko",
        "size_standard": "KS"
    }
    create_project = client.post("/api/v1/projects", json=project_payload)
    assert create_project.status_code == 200
    project_id = create_project.json()["id"]

    list_projects = client.get("/api/v1/projects")
    assert list_projects.status_code == 200
    assert any(p["id"] == project_id for p in list_projects.json())

    session_payload = {
        "project_id": project_id,
        "session_title": "Test Session",
        "description": "Session without auto pipeline",
        "user_keywords": ["spring", "casual"],
        "auto_start": False
    }
    create_session = client.post("/api/v1/sessions", json=session_payload)
    assert create_session.status_code == 200
    session_id = create_session.json()["id"]

    session_status = client.get(f"/api/v1/sessions/{session_id}/status")
    assert session_status.status_code == 200
    assert session_status.json()["status"] in ["created", "running", "cancelled", "failed", "completed"]
