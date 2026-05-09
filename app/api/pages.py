"""
HTML page router - serves Jinja2 templates for the frontend.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


def _render(request: Request, template: str, **context) -> HTMLResponse:
    return templates.TemplateResponse(request, template, context)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(url="/projects", status_code=307)


@router.get("/workspace", response_class=HTMLResponse)
def workspace_home(request: Request):
    return RedirectResponse(url="/projects", status_code=307)


@router.get("/workspace/settings", response_class=HTMLResponse)
def workspace_settings(request: Request):
    return _render(request, "pages/settings.html")


@router.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    return _render(request, "pages/projects.html")


@router.get("/projects/new", response_class=HTMLResponse)
def new_project(request: Request):
    return _render(request, "pages/new_project.html")


@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(request: Request, project_id: uuid.UUID):
    return _render(request, "pages/project_detail.html", project_id=str(project_id))


@router.get("/sessions/{session_id}", response_class=HTMLResponse)
def session_workspace(request: Request, session_id: uuid.UUID):
    return _render(request, "pages/session_detail.html", session_id=str(session_id))


@router.get("/library", response_class=HTMLResponse)
def library(request: Request):
    return _render(request, "pages/library.html")
