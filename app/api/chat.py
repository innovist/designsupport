"""
Chat API endpoints for Fashion AI Generation System
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.settings_storage import get_gemini_model
from app.api.projects import project_exists, get_project_snapshot
from app.services.chat_store import (
    create_chat_session,
    list_chat_sessions,
    get_chat_session,
    add_chat_message,
    list_chat_messages
)
from ai_clients.gemini_client import GeminiClient

router = APIRouter()
gemini_client = GeminiClient()


class ChatSessionCreate(BaseModel):
    project_id: int = Field(..., ge=1)
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: int
    project_id: int
    title: Optional[str]
    created_at: str
    updated_at: str


class ChatMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    message: str
    created_at: str


def _ensure_gemini_ready() -> None:
    settings = get_settings()
    if not settings.gemini_api_key or settings.gemini_api_key == "test-gemini-key":
        raise HTTPException(
            status_code=503,
            detail="Gemini API key is not configured"
        )


def _build_chat_prompt(
    project: Optional[Dict[str, Any]],
    history: List[Dict[str, Any]],
    user_message: str
) -> str:
    context_lines = []
    if project:
        context_lines.append(f"프로젝트 제목: {project.get('title')}")
        if project.get("description"):
            context_lines.append(f"프로젝트 설명: {project.get('description')}")
        if project.get("prompt"):
            context_lines.append(f"분석 목표: {project.get('prompt')}")

    history_lines = [
        f"{'사용자' if m['role'] == 'user' else 'AI'}: {m['message']}"
        for m in history[-10:]
    ]

    context = "\n".join(context_lines) if context_lines else "프로젝트 맥락 없음"
    history_text = "\n".join(history_lines) if history_lines else "이전 대화 없음"

    return (
        "너는 패션 트렌드/디자인 전문 AI 어시스턴트다. "
        "정확하고 간결하게 답하고, 확인되지 않은 사실은 추측하지 말아라. "
        "모든 답변은 한국어로 작성한다.\n\n"
        f"{context}\n\n"
        f"대화 기록:\n{history_text}\n\n"
        f"사용자: {user_message}\nAI:"
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_sessions() -> List[Dict[str, Any]]:
    return list_chat_sessions()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(payload: ChatSessionCreate) -> Dict[str, Any]:
    if not project_exists(payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return create_chat_session(payload.project_id, payload.title)


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(session_id: int) -> List[Dict[str, Any]]:
    session = get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return list_chat_messages(session_id)


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(session_id: int, payload: ChatMessageCreate) -> Dict[str, Any]:
    session = get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    _ensure_gemini_ready()

    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    add_chat_message(session_id, "user", user_message)

    history = list_chat_messages(session_id)[:-1]
    project = get_project_snapshot(session.get("project_id"))
    prompt = _build_chat_prompt(project, history, user_message)

    response = await gemini_client.generate_content(
        prompt=prompt,
        model=get_gemini_model()
    )
    assistant_message = response.text.strip()
    if not assistant_message:
        raise HTTPException(status_code=502, detail="Empty response from Gemini")

    return add_chat_message(session_id, "assistant", assistant_message)
